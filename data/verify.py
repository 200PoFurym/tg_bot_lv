import asyncio
import face_recognition
import os
import logging
import cv2
import numpy as np
import random
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from main import bot, i18n
from models import User

router = Router()

class VerificationStates(StatesGroup):
    waiting_for_gesture_photo = State()

def detect_face_face_recognition(image):
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_image)
    return face_locations

def encode_face_face_recognition(image, face_location):
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(rgb_image, [face_location])
    return face_encodings[0] if face_encodings else None

def detect_and_compare_faces(reference_photo_path, current_photo_path):
    reference_image = cv2.imread(reference_photo_path)
    current_image = cv2.imread(current_photo_path)

    reference_face_locations = detect_face_face_recognition(reference_image)
    current_face_locations = detect_face_face_recognition(current_image)

    if len(reference_face_locations) == 0 or len(current_face_locations) == 0:
        return False

    reference_face_encoding = encode_face_face_recognition(reference_image, reference_face_locations[0])
    current_face_encoding = encode_face_face_recognition(current_image, current_face_locations[0])

    if reference_face_encoding is None or current_face_encoding is None:
        return False

    results = face_recognition.compare_faces([reference_face_encoding], current_face_encoding)
    return results[0]

def preprocess_image(image):
    if image is None:
        raise ValueError("Изображение не загружено")

    if len(image.shape) == 2:
        gray = image
    elif len(image.shape) == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 3 and image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        raise ValueError(f"Неизвестный формат изображения с {image.shape[2]} каналами")

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    threshold_image = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY_INV, 11, 2)

    return threshold_image

def find_valid_contours(threshold_image):
    contours, _ = cv2.findContours(threshold_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours is None or len(contours) == 0:
        raise ValueError("Не удалось найти контуры.")

    valid_contours = [c for c in contours if cv2.contourArea(c) > 100]
    valid_contours = [c for c in valid_contours if cv2.arcLength(c, True) > 100]

    return valid_contours

def compute_defects(contour):
    hull = cv2.convexHull(contour, returnPoints=False)
    if len(contour) < 3 or hull is None:
        return None
    return cv2.convexityDefects(contour, hull)

def count_fingers(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    try:
        contours = find_valid_contours(thresh)
    except Exception as e:
        logging.error(f"Ошибка при нахождении контуров: {e}")
        return 0

    if not contours:
        logging.info("Контуры не найдены.")
        return 0

    max_contour = max(contours, key=cv2.contourArea)
    defects = compute_defects(max_contour)

    if defects is None or len(defects) == 0:
        logging.info("Нет дефектов.")
        return 0

    finger_count = 0
    for i in range(defects.shape[0]):
        s, e, f, _ = defects[i, 0]
        start, end, far = tuple(max_contour[s][0]), tuple(max_contour[e][0]), tuple(max_contour[f][0])

        a, b, c = np.linalg.norm(np.array(start) - np.array(far)), np.linalg.norm(np.array(end) - np.array(far)), np.linalg.norm(np.array(start) - np.array(end))
        angle = np.arccos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c))

        if angle <= np.pi / 2:
            finger_count += 1

    return finger_count

def load_image_from_bytes(photo_bytes):
    np_arr = np.frombuffer(photo_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Не удалось декодировать изображение")
    return image

async def verify_gesture(photo_bytes: bytes, selected_gesture: str) -> tuple[bool, np.ndarray]:
    image = load_image_from_bytes(photo_bytes)
    preprocessed_image = preprocess_image(image)

    if selected_gesture == i18n.gettext('покажите два пальца'):
        result = count_fingers(preprocessed_image) == 2
    elif selected_gesture == i18n.gettext('сделайте знак ОК'):
        result = count_fingers(preprocessed_image) == 2
    elif selected_gesture == i18n.gettext('покажите ладонь'):
        result = count_fingers(preprocessed_image) >= 5
    elif selected_gesture == i18n.gettext('покажите знак класс'):
        result = True
    else:
        result = False

    return result, image

@router.message(F.text == i18n.gettext('Верификация'))
async def request_gesture_photo(message: types.Message, state: FSMContext):
    gestures = [
        i18n.gettext('покажите два пальца'),
        i18n.gettext('покажите знак класс'),
        i18n.gettext('сделайте знак ОК'),
        i18n.gettext('покажите ладонь')
    ]
    selected_gesture = random.choice(gestures)
    await state.update_data(selected_gesture=selected_gesture)
    await message.reply(i18n.gettext(f"Для верификации, пожалуйста, {selected_gesture} и отправьте фото."))
    await state.set_state(VerificationStates.waiting_for_gesture_photo)

def save_photo(photo_bytes, filename):
    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'wb') as f:
        f.write(photo_bytes)

@router.message(F.photo, VerificationStates.waiting_for_gesture_photo)
async def handle_photo(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        selected_gesture = data.get('selected_gesture')

        if not selected_gesture:
            await message.reply(i18n.gettext('Сначала запросите верификацию с жестом.'))
            return

        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        await asyncio.sleep(1)
        file = await bot.download_file(file_path)
        photo_bytes = file.read()

        if not photo_bytes:
            await message.reply(i18n.gettext('Не удалось получить фото. Попробуйте снова.'))
            return

        current_photo_path = 'current_photo.jpg'
        save_photo(photo_bytes, current_photo_path)

        verification_result, _ = await verify_gesture(photo_bytes, selected_gesture)

        if verification_result:
            await message.reply(i18n.gettext("Жест успешно распознан"))
        else:
            await message.reply(i18n.gettext("Жест не распознан. Попробуйте снова"))
            return

        user = await User.get(user_id=message.from_user.id)
        if user and user.file_url:
            try:
                await asyncio.sleep(3)
                logging.info(f"Using file_id: {user.file_url}")
                file_id = user.file_id
                file_info = await bot.get_file(file_id)
                file = await bot.download_file(file_info.file_path)
                reference_photo_bytes = file.getvalue()
                reference_photo_path = 'reference_photo.jpg'
                save_photo(reference_photo_bytes, reference_photo_path)
            except Exception as e:
                logging.error(f"Ошибка при загрузке файла: {str(e)}")
                await message.reply(i18n.gettext("Ошибка при загрузке файла для сравнения с лицом."))
                return

            is_face_match = detect_and_compare_faces(reference_photo_path, current_photo_path)
            if is_face_match:
                await message.reply(i18n.gettext("Лицо успешно подтверждено. Верификация пройдена"))
            else:
                await message.reply(i18n.gettext("Лицо не совпадает. Попробуйте снова."))

        await state.clear()

    except Exception as e:
        logging.error(f"Ошибка при обработке фото: {e}")
        await message.reply(i18n.gettext("Произошла ошибка при обработке вашего фото. Попробуйте снова."))
