from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardRemove
from tortoise.exceptions import DoesNotExist

from handlers.registration import return_main, begin_registration
from keyboards import reply_kb
from keyboards.reply_kb import main_menu_kb
from models import LeomatchMain, LeomatchRegistration, LeomatchChange, User
from main import i18n
from shortcuts import get_leo, show_profile_db, update_profile
from aiogram.fsm.context import FSMContext
import re

router = Router()

def escape_md(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)






async def start(message: types.Message, state: FSMContext):
    await show_profile_db(message, message.from_user.id, reply_kb.get_numbers(4, True))
    await message.answer(
        i18n.gettext("1. Отредактировать мой профиль.\n2. Изменить фото/видео.\n3. Изменить текст профиля.\n4. Просмотреть профили"),
        reply_markup=reply_kb.get_numbers(4, True)
    )
    await state.set_state(LeomatchMain.PROFILE_MANAGE)

@router.message(F.text == "1", LeomatchMain.WAIT)
async def edit_profile(message: types.Message, state: FSMContext):
    leo = await get_leo(message.from_user.id)
    if not leo.active or not leo.search:
        await update_profile(message.from_user.id, {"active": True, "search": True})
    await start(message, state)

@router.message(F.text == "2", LeomatchMain.WAIT)
async def change_photo_video(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.text == i18n.gettext("Выйти"), F.state_in([LeomatchMain.WAIT, LeomatchMain.PROFILE_MANAGE]))
async def exit(message: types.Message, state: FSMContext):
    await return_main(message, state)

@router.message(F.text == "3", LeomatchMain.WAIT)
async def deactivate_profile(message: types.Message, state: FSMContext):
    await message.answer(
        i18n.gettext("Тогда ты не будешь знать, кому ты нравишься... Уверены насчет деактивации?\n\n1. Да, деактивируйте мой профиль, пожалуйста.\n2. Нет, я хочу посмотреть свои матчи."),
        reply_markup=reply_kb.get_numbers(2)
    )
    await state.set_state(LeomatchMain.SLEEP)

@router.message(F.text == "1", LeomatchMain.SLEEP)
async def confirm_deactivation(message: types.Message, state: FSMContext):
    await message.answer(
        i18n.gettext("Надеюсь, вы встретили кого-нибудь с моей помощью! \nВсегда рад пообщаться. Если скучно, напиши мне - я найду для тебя кого-то особенного.\n\n1. Просмотр профилей"),
        reply_markup=reply_kb.get_numbers(1)
    )
    await update_profile(message.from_user.id, {"active": False, "search": False})
    await state.set_state(LeomatchMain.WAIT)

@router.message(F.text == "2", LeomatchMain.SLEEP)
async def view_profiles(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.text == "1", LeomatchMain.PROFILE_MANAGE)
async def edit_profile_start(message: types.Message, state: FSMContext):
    await begin_registration(message, state)

@router.message(F.text == "2", LeomatchMain.PROFILE_MANAGE)
async def upload_photo_video(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Отправьте фото или видео (до 15 сек)"), reply_markup=reply_kb.cancel())
    await state.set_state(LeomatchMain.SET_PHOTO)

@router.message(F.text == "3", LeomatchMain.PROFILE_MANAGE)
async def set_description(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Введите новый текст профиля"), reply_markup=reply_kb.cancel())
    await state.set_state(LeomatchMain.SET_DESCRIPTION)

@router.message(F.text == "4", LeomatchMain.PROFILE_MANAGE)
async def view_profiles_again(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.text == i18n.gettext("Отменить"), LeomatchMain.SET_DESCRIPTION)
async def cancel_description(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(LeomatchMain.SET_DESCRIPTION)
async def update_description(message: types.Message, state: FSMContext):
    await update_profile(message.from_user.id, {"about_me": message.text})
    await start(message, state)

@router.message(F.text == i18n.gettext("Отменить"), LeomatchMain.SET_PHOTO)
async def cancel_photo(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(LeomatchMain.SET_PHOTO)
async def update_photo(message: types.Message, state: FSMContext):
    file_url = ""
    media_type = ""
    if message.photo:
        file_url = message.photo[-1].file_id
        media_type = "PHOTO"
    elif message.video:
        if message.video.duration > 15:
            await message.answer(i18n.gettext("Пожалуйста, пришли видео не более 15 секунд"))
            return
        file_url = message.video.file_id
        media_type = "VIDEO"
    elif message.video_note:
        if message.video_note.duration > 15:
            await message.answer(i18n.gettext("Пожалуйста, пришли видео не более 15 секунд"))
            return
        file_url = message.video_note.file_id
        media_type = "VIDEO_NOTE"
    await update_profile(message.from_user.id, {"file_url": file_url, "media_type": media_type})
    await start(message, state)



@router.message(F.text == i18n.gettext("Изменить анкету"))
async def handle_change_profile(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Вы выбрали изменить анкету. Пожалуйста, введите новое имя:"), reply_markup=ReplyKeyboardRemove())
    await state.set_state(LeomatchChange.CHANGE_NAME)

@router.message(F.text, LeomatchChange.CHANGE_NAME)
async def process_name_change(message: types.Message, state: FSMContext):
    new_name = message.text
    user_id = message.from_user.id
    try:
        user = await User.get(user_id=user_id)
        user.full_name = new_name
        await user.save()
        await message.answer(i18n.gettext(f"Ваше имя изменено на {escape_md(new_name)}. Введите ваш новый возраст:"), reply_markup=ReplyKeyboardRemove())
        await state.set_state(LeomatchChange.CHANGE_AGE)
    except DoesNotExist:
        await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))

@router.message(F.text, LeomatchChange.CHANGE_AGE)
async def process_age_change(message: types.Message, state: FSMContext):
    try:
        new_age = int(message.text)
        user_id = message.from_user.id
        try:
            user = await User.get(user_id=user_id)
            user.age = new_age
            await user.save()
            await message.answer(i18n.gettext(f"Ваш возраст изменен на {new_age}. Введите минимальный возраст для поиска:"), reply_markup=ReplyKeyboardRemove())
            await state.set_state(LeomatchChange.CHANGE_MIN_AGE)
        except DoesNotExist:
            await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))
    except ValueError:
        await message.answer(i18n.gettext("Пожалуйста, введите корректный возраст."))

@router.message(F.text, LeomatchChange.CHANGE_MIN_AGE)
async def process_min_age_change(message: types.Message, state: FSMContext):
    try:
        new_min_age = int(message.text)
        user_id = message.from_user.id
        try:
            user = await User.get(user_id=user_id)
            user.min_age = new_min_age
            await user.save()
            await message.answer(i18n.gettext(f"Минимальный возраст изменен на {new_min_age}. Введите максимальный возраст для поиска:"), reply_markup=ReplyKeyboardRemove())
            await state.set_state(LeomatchChange.CHANGE_MAX_AGE)
        except DoesNotExist:
            await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))
    except ValueError:
        await message.answer(i18n.gettext("Пожалуйста, введите корректный возраст."))

@router.message(F.text, LeomatchChange.CHANGE_MAX_AGE)
async def process_max_age_change(message: types.Message, state: FSMContext):
    try:
        new_max_age = int(message.text)
        user_id = message.from_user.id
        try:
            user = await User.get(user_id=user_id)
            user.max_age = new_max_age
            await user.save()
            await message.answer(i18n.gettext(f"Максимальный возраст изменен на {new_max_age}. Введите ваш новый город:"), reply_markup=ReplyKeyboardRemove())
            await state.set_state(LeomatchChange.CHANGE_CITY)
        except DoesNotExist:
            await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))
    except ValueError:
        await message.answer(i18n.gettext("Пожалуйста, введите корректный возраст."))

@router.message(F.text, LeomatchChange.CHANGE_CITY)
async def process_city_change(message: types.Message, state: FSMContext):
    new_city = message.text
    user_id = message.from_user.id
    try:
        user = await User.get(user_id=user_id)
        user.city = new_city
        await user.save()
        await message.answer(i18n.gettext(f"Ваш город изменен на {escape_md(new_city)}."))
        await message.answer(i18n.gettext('Введите ваш новый адрес:', reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=i18n.gettext("Отправить местоположение"), request_location=True)]], resize_keyboard=True)))
        await state.set_state(LeomatchChange.CHANGE_ADDRESS)
    except DoesNotExist:
        await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))

@router.message(F.text, LeomatchChange.CHANGE_ADDRESS)
async def process_address_change(message: types.Message, state: FSMContext):
    new_address = message.text
    user_id = message.from_user.id
    try:
        user = await User.get(user_id=user_id)
        user.address = new_address
        await user.save()
        await message.answer(i18n.gettext(f"Ваш адрес изменен на {escape_md(new_address)}. Введите, кого вы ищете:"), reply_markup=ReplyKeyboardRemove())
        await state.set_state(LeomatchChange.CHANGE_ABOUT_ME)
    except DoesNotExist:
        await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))

@router.message(F.text, LeomatchChange.CHANGE_ABOUT_ME)
async def process_about_me_change(message: types.Message, state: FSMContext):
    about_me = message.text
    user_id = message.from_user.id
    try:
        user = await User.get(user_id=user_id)
        user.about_me = about_me
        await user.save()
        await message.answer(i18n.gettext(f"Информация о себе обновлена. Пришлите новое фото или видео:"), reply_markup=ReplyKeyboardRemove())
        await state.set_state(LeomatchChange.CHANGE_PHOTO)
    except DoesNotExist:
        await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))

@router.message(F.photo | F.video, LeomatchChange.CHANGE_PHOTO)
async def process_photo_video_change(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        user = await User.get(user_id=user_id)
        if message.photo:
            user.photo = message.photo[-1].file_id
        elif message.video:
            user.video = message.video.file_id
        await user.save()
        await message.answer(i18n.gettext("Ваше фото или видео обновлено. Регистрация завершена."), reply_markup=main_menu_kb())
        await state.clear()
    except DoesNotExist:
        await message.answer(i18n.gettext("Ошибка: Пользователь не найден."))