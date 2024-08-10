from aiogram import types, F, Router
from handlers.registration import return_main, begin_registration
from keyboards import reply_kb
from models import LeomatchMain
from main import i18n
from shortcuts import get_leo, show_profile_db, update_profile
from aiogram.fsm.context import FSMContext

router = Router()

async def start(message: types.Message, state: FSMContext):
    await show_profile_db(message, message.from_user.id, reply_kb.get_numbers(4, True))
    await message.answer(
        i18n.gettext("1. Отредактировать мой профиль.\n2. Изменить фото/видео.\n3. Изменить текст профиля.\n4. Просмотреть профили"),
        reply_markup=reply_kb.get_numbers(4, True)
    )
    await state.set_state(LeomatchMain.PROFILE_MANAGE)

@router.message(F.text == "1", F.state(LeomatchMain.WAIT))
async def edit_profile(message: types.Message, state: FSMContext):
    leo = await get_leo(message.from_user.id)
    if not leo.active or not leo.search:
        await update_profile(message.from_user.id, {"active": True, "search": True})
    await start(message, state)

@router.message(F.text == "2", F.state(LeomatchMain.WAIT))
async def change_photo_video(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.text == i18n.gettext("Выйти"), F.state.in_([LeomatchMain.WAIT, LeomatchMain.PROFILE_MANAGE]))
async def exit(message: types.Message, state: FSMContext):
    await return_main(message, state)

@router.message(F.text == "3", F.state(LeomatchMain.WAIT))
async def deactivate_profile(message: types.Message, state: FSMContext):
    await message.answer(
        i18n.gettext("Тогда ты не будешь знать, кому ты нравишься... Уверены насчет деактивации?\n\n1. Да, деактивируйте мой профиль, пожалуйста.\n2. Нет, я хочу посмотреть свои матчи."),
        reply_markup=reply_kb.get_numbers(2)
    )
    await state.set_state(LeomatchMain.SLEEP)

@router.message(F.text == "1", F.state(LeomatchMain.SLEEP))
async def confirm_deactivation(message: types.Message, state: FSMContext):
    await message.answer(
        i18n.gettext("Надеюсь, вы встретили кого-нибудь с моей помощью! \nВсегда рад пообщаться. Если скучно, напиши мне - я найду для тебя кого-то особенного.\n\n1. Просмотр профилей"),
        reply_markup=reply_kb.get_numbers(1)
    )
    await update_profile(message.from_user.id, {"active": False, "search": False})
    await state.set_state(LeomatchMain.WAIT)

@router.message(F.text == "2", F.state(LeomatchMain.SLEEP))
async def view_profiles(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.text == "1", F.state(LeomatchMain.PROFILE_MANAGE))
async def edit_profile_start(message: types.Message, state: FSMContext):
    await begin_registration(message, state)

@router.message(F.text == "2", F.state(LeomatchMain.PROFILE_MANAGE))
async def upload_photo_video(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Отправьте фото или видео (до 15 сек)"), reply_markup=reply_kb.cancel())
    await state.set_state(LeomatchMain.SET_PHOTO)

@router.message(F.text == "3", F.state(LeomatchMain.PROFILE_MANAGE))
async def set_description(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Введите новый текст профиля"), reply_markup=reply_kb.cancel())
    await state.set_state(LeomatchMain.SET_DESCRIPTION)

@router.message(F.text == "4", F.state(LeomatchMain.PROFILE_MANAGE))
async def view_profiles_again(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.text == i18n.gettext("Отменить"), F.state(LeomatchMain.SET_DESCRIPTION))
async def cancel_description(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.state(LeomatchMain.SET_DESCRIPTION))
async def update_description(message: types.Message, state: FSMContext):
    await update_profile(message.from_user.id, {"about_me": message.text})
    await start(message, state)

@router.message(F.text == i18n.gettext("Отменить"), F.state(LeomatchMain.SET_PHOTO))
async def cancel_photo(message: types.Message, state: FSMContext):
    await start(message, state)

@router.message(F.state(LeomatchMain.SET_PHOTO))
async def update_photo(message: types.Message, state: FSMContext):
    photo = ""
    media_type = ""
    if message.photo:
        photo = message.photo[-1].file_id
        media_type = "PHOTO"
    elif message.video:
        if message.video.duration > 15:
            await message.answer(i18n.gettext("Пожалуйста, пришли видео не более 15 секунд"))
            return
        photo = message.video.file_id
        media_type = "VIDEO"
    elif message.video_note:
        if message.video_note.duration > 15:
            await message.answer(i18n.gettext("Пожалуйста, пришли видео не более 15 секунд"))
            return
        photo = message.video_note.file_id
        media_type = "VIDEO_NOTE"
    await update_profile(message.from_user.id, {"photo": photo, "media_type": media_type})
    await start(message, state)
