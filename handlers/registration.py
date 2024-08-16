import io
import logging
import os
import cv2
import numpy as np
from aiogram import types, F, Router
from aiogram.filters import Command
from geopy import Nominatim
from keyboards.reply_kb import main_menu_kb, chooice_sex, which_search, yes_no
from models import User, LeomatchRegistration
from main import i18n, bot
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone


geolocator = Nominatim(user_agent="YOUR_USER_AGENT")
router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

opencv_path = os.path.dirname(cv2.__file__)

haarcascades_path = os.path.join(opencv_path, 'data')
haar_cascade_path = os.path.join(haarcascades_path, 'haarcascade_frontalface_default.xml')

async def get_face_encoding(photo_bytes):
    try:
        np_arr = np.frombuffer(photo_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(haar_cascade_path)
        faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            return None

        (x, y, w, h) = faces[0]
        face_image = image[y:y+h, x:x+w]
        face_encoding = cv2.resize(face_image, (128, 128))
        return face_encoding.flatten()

    except Exception as e:
        logger.error(f"Error in get_face_encoding: {e}")
        return None


@router.message(F.text == i18n.gettext("Давай, начнем!"))
async def bot_start(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Настоятельно рекомендуем указать username или в настройках разрешение на пересылку сообщения иначе вам не смогут написать те, кого вы лайкнете"))
    await begin_registration(message, state)

@router.message(F.text == i18n.gettext("Отменить"), LeomatchRegistration.AGE)
async def cancel_registration(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Регистрация отменена!"))
    await return_main(message, state)

async def return_main(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Вы успешно отменили регистрацию! Возвращаемся в главное меню."), reply_markup=main_menu_kb())
    await state.clear()


@router.message(Command(commands=['start', 'help']))
async def handle_start_and_help(message: types.Message, state: FSMContext):
    logger.info(f"Команда {message.text} получена.")
    user_id = message.from_user.id
    command_parts = message.text.split(maxsplit=1)
    command = command_parts[0]
    referral_code = command_parts[1].strip().upper() if len(command_parts) > 1 else None

    try:
        user = await User.get_or_none(user_id=user_id)

        if command.startswith('/start'):
            if referral_code:
                referrer = await User.get_or_none(referral_code=referral_code)
                if referrer:
                    referrer.profile_views += 20
                    referrer.views_expiry_date = datetime.now(timezone.utc) + timedelta(days=1)
                    await referrer.save()
                    await message.reply(
                        i18n.gettext("Вы получили 20 дополнительных просмотров за использование реферального кода!"))

            if user:
                if user.is_registered:
                    await message.reply(i18n.gettext("Добро пожаловать обратно!"), reply_markup=main_menu_kb())
                else:
                    await state.set_state(LeomatchRegistration.START)
                    await message.reply(i18n.gettext("Вы не завершили регистрацию. Давайте начнем с вашего возраста."),
                                        reply_markup=main_menu_kb())
                    await state.set_state(LeomatchRegistration.AGE)
                    await message.reply('Сколько вам лет?')
            else:
                await state.set_state(LeomatchRegistration.START)
                await message.reply(i18n.gettext("Вы не зарегистрированы. Давайте начнем с вашего возраста."),
                                    reply_markup=main_menu_kb())
                await state.set_state(LeomatchRegistration.AGE)
                await message.reply('Сколько вам лет?')

        elif command.startswith('/help'):
            await message.reply(i18n.gettext("Команда /help предоставляет информацию о том, как использовать бота."))

    except Exception as e:
        await message.reply(f"Ошибка в обработчике handle_start_and_help: {e}")




@router.message(LeomatchRegistration.START)
async def start(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    if current_state == LeomatchRegistration.START:
        await message.reply('Сколько вам лет?')
        await state.set_state(LeomatchRegistration.AGE)
        return
    await state.set_state(LeomatchRegistration.AGE)

@router.message(F.text, LeomatchRegistration.AGE)
async def begin_registration(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    try:
        age = message.text
        if not age.isdigit():
            await message.answer(i18n.gettext('Пожалуйста, введите возраст цифрами.'))
            return

        await state.update_data(age=int(age))
        await message.answer(i18n.gettext('Теперь укажите минимальный возраст партнера.'))
        await state.set_state(LeomatchRegistration.MIN_AGE)
        current_state = await state.get_state()
        logger.info(f"Received message: {message.text}, State: {current_state}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике begin_registration: {e}")
        await message.answer(i18n.gettext('Произошла ошибка при обработке вашего запроса. Попробуйте снова позже.'))



@router.message(F.text, LeomatchRegistration.MIN_AGE)
async def set_min_age(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    try:
        min_age = int(message.text)
        await state.update_data(min_age=min_age)
        await message.answer(i18n.gettext("Теперь выберите максимальный возраст партнера."))
        await state.set_state(LeomatchRegistration.MAX_AGE)
    except ValueError:
        await message.answer(i18n.gettext("Пожалуйста, введите возраст цифрами."))

@router.message(F.text, LeomatchRegistration.MAX_AGE)
async def set_max_age(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    try:
        max_age = int(message.text)
        data = await state.get_data()
        min_age = data.get('min_age')
        if max_age < min_age:
            await message.answer(i18n.gettext("Максимальный возраст не может быть меньше минимального. Попробуйте снова."))
            return
        await state.update_data(max_age=max_age)
        await message.answer(i18n.gettext("Возрастной диапазон установлен. Теперь укажите город, в котором вы находитесь."))
        await state.set_state(LeomatchRegistration.CITY)
    except ValueError:
        await message.answer(i18n.gettext("Пожалуйста, введите возраст цифрами."))


@router.message(F.text, LeomatchRegistration.CITY)
async def set_city(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    city = message.text.strip()
    await state.update_data(city=city)

    await message.answer(
        i18n.gettext("Теперь укажите ваше местоположение. Нажмите на кнопку, чтобы отправить геопозицию:"),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=i18n.gettext("Отправить местоположение"), request_location=True)]
            ], resize_keyboard=True
        ))
    await state.set_state(LeomatchRegistration.ADDRESS)


@router.message(F.location, LeomatchRegistration.ADDRESS)
async def handle_location(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    latitude = message.location.latitude
    longitude = message.location.longitude

    location = geolocator.reverse((latitude, longitude))
    address = location.address if location else "Неизвестный адрес"

    await state.update_data(latitude=latitude, longitude=longitude, address=address)

    await message.answer(i18n.gettext(f"Ваше местоположение установлено: {address}."))
    await message.answer(i18n.gettext("Укажите ваше полное имя:"))
    await state.set_state(LeomatchRegistration.FULL_NAME)

@router.message(F.text, LeomatchRegistration.FULL_NAME)
async def set_full_name(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    name = message.text.strip()
    if len(name) > 15:
        await message.answer(i18n.gettext("Пожалуйста, введите имя не более 15 символов."))
        return
    await state.update_data(full_name=name)
    await message.answer(i18n.gettext("Укажите ваш пол"), reply_markup=chooice_sex())
    await state.set_state(LeomatchRegistration.SEX)


@router.message(F.text.in_([i18n.gettext("Я парень"), i18n.gettext("Я девушка")]), LeomatchRegistration.SEX)
async def set_sex(message: types.Message, state: FSMContext):
    sex = "MALE" if message.text == i18n.gettext("Я парень") else "FEMALE"
    await state.update_data(sex=sex)
    await message.answer(
        i18n.gettext("Что вы ищете? Парня, Девушку, Все равно"),
        reply_markup=which_search()
    )
    await state.set_state(LeomatchRegistration.WHICH_SEARCH)

@router.message(F.text.in_([i18n.gettext("Парня"), i18n.gettext("Девушку"), i18n.gettext("Мне всё равно")]), LeomatchRegistration.WHICH_SEARCH)
async def set_search_preference(message: types.Message, state: FSMContext):
    preferences = {
        i18n.gettext("Парня"): "MALE",
        i18n.gettext("Девушку"): "FEMALE",
        i18n.gettext("Мне всё равно"): "ANY"
    }
    await state.update_data(which_search=preferences[message.text])
    await message.answer(i18n.gettext("Напишите что-нибудь о себе."))
    await state.set_state(LeomatchRegistration.ABOUT_ME)

@router.message(F.text, LeomatchRegistration.WHICH_SEARCH)
async def set_which_search(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    which_search = message.text.strip()
    if which_search.lower() not in ['парня', 'девушку', 'все равно']:
        await message.answer(i18n.gettext("Пожалуйста, введите 'Парня', 'Девушку' или 'Все равно'."))
        return
    await state.update_data(which_search=which_search)
    await message.answer(i18n.gettext("Напишите что-нибудь о себе."))
    await state.set_state(LeomatchRegistration.ABOUT_ME)

@router.message(F.text, LeomatchRegistration.ABOUT_ME)
async def set_about_me(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Received message: {message.text}, State: {current_state}")
    about_me = message.text.strip()
    await state.update_data(about_me=about_me)
    await message.answer(i18n.gettext("Теперь пришлите фото или запишите видео до 15 секунд."))
    await state.set_state(LeomatchRegistration.SEND_PHOTO)

@router.message(F.photo, LeomatchRegistration.SEND_PHOTO)
async def handle_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    photo_bytes_io = await bot.download(file_id)
    photo_bytes = photo_bytes_io.getvalue()
    face_encoding = await get_face_encoding(photo_bytes)

    if face_encoding is None:
        await message.answer(i18n.gettext("Не удалось распознать лицо. Пожалуйста, попробуйте снова."))
        return

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'

    await save_media(message, state, file_id, file_url, "photo", face_encoding)


@router.message(F.video, LeomatchRegistration.SEND_PHOTO)
async def handle_video(message: types.Message, state: FSMContext):
    file_id = message.video.file_id
    photo_bytes_io = await bot.download(file_id)
    photo_bytes = photo_bytes_io.getvalue()
    face_encoding = await get_face_encoding(photo_bytes)

    if face_encoding is None:
        await message.answer(i18n.gettext("Не удалось распознать лицо. Пожалуйста, попробуйте снова."))
        return

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'

    await save_media(message, state, file_id, file_url, "video", face_encoding)

async def save_media(message: types.Message, state: FSMContext, file_id: str, file_url: str, media_type: str, face_encoding: np.ndarray):
    await state.update_data(file_id=file_id, file_url=file_url, media_type=media_type, face_encoding=face_encoding.tolist())
    await message.answer(i18n.gettext("Ваше фото/видео сохранено. Вы готовы завершить регистрацию? (Да/Нет)"), reply_markup=yes_no())
    await state.set_state(LeomatchRegistration.FINAL)

@router.message(F.text, LeomatchRegistration.FINAL)
async def finalize_registration(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Current state before clearing: {current_state}")
    if message.text.lower() == i18n.gettext("да"):
        data = await state.get_data()
        user_id = message.from_user.id
        await User.update_or_create(
            user_id=user_id,
            defaults={
                'full_name': data.get('full_name'),
                'age': data.get('age'),
                'min_age': data.get('min_age'),
                'max_age': data.get('max_age'),
                'city': data.get('city'),
                'address': data.get('address'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'sex': data.get('sex'),
                'which_search': data.get('which_search'),
                'about_me': data.get('about_me'),
                'media_type': data.get('media_type'),
                'file_url': data.get('file_url'),
                'file_id': data.get('file_id'),
                'is_registered': True,
                'reference_face_encoding': data.get('face_encoding')
            }
        )
        await message.answer(i18n.gettext("Ваша регистрация завершена! Теперь вы можете искать и просматривать профили других пользователей."), reply_markup=main_menu_kb())
        await state.clear()
    elif message.text.lower() == i18n.gettext("нет"):
        await message.answer(i18n.gettext("Регистрация отменена."), reply_markup=main_menu_kb())
        await state.clear()
    else:
        await message.answer(i18n.gettext("Пожалуйста, ответьте 'Да' или 'Нет'."), reply_markup=yes_no())

