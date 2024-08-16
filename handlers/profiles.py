from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import lazy_gettext as __
from handlers.start import manage

from models import LeomatchProfiles
from main import bot, i18n
from shortcuts import (
    bot_show_profile_db, clear_all_likes, delete_like, get_leo,
    get_leos_id, get_first_like, leo_set_like, show_media, show_profile_db
)
from keyboards.inline_kb import profile_alert, profile_alert_action, profile_like_action, profile_view_action, write_profile
from keyboards.reply_kb import cancel
from data.callback_datas import LeomatchLikeAction, LeomatchProfileAction, LeomatchProfileAlert, LikeActionEnum, ProfileActionEnum


router = Router()

async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔍", reply_markup=types.ReplyKeyboardRemove())
    leos = await get_leos_id(message.from_user.id)
    await state.update_data({"leos": leos})
    await next(message, state)

async def next(message: types.Message, state: FSMContext):
    data = await state.get_data()
    leos = data.get("leos")
    if leos:
        current = leos.pop(0)
        await state.update_data(leos=leos)
        await show_profile_db(message, current, keyboard=profile_view_action(current))
        await state.set_state(LeomatchProfiles.LOOCK)
    else:
        await message.answer(i18n.gettext("Нет больше пользователей"))
        await manage(message, state)

async def next_like(message: types.Message, state: FSMContext):
    data = await state.get_data()
    me = data.get("me")
    if not me:
        me = message.from_user.id
    leo = await get_first_like(me)
    if leo:
        user_leo = await leo.from_user
        user = await user_leo.user
        try:
            await show_profile_db(message, user.uid, profile_like_action(user.uid), leo.message)
            await state.set_state(LeomatchProfiles.MANAGE_LIKE)
        except Exception:
            await delete_like(user.uid, me)
            await next_like(message, state)
    else:
        leo_me = await get_leo(me)
        if not leo_me:
            await message.answer(i18n.gettext("Произошла ошибка"))
            await state.clear()
            return
        await state.clear()
        await message.answer(i18n.gettext("Нет больше лайков"))
        leo_me.count_likes = 0
        await leo_me.save()

async def like(message: types.Message, state: FSMContext, from_uid: int, to_uid: int, msg: str = None):
    await message.answer(i18n.gettext("Лайк отправлен"), reply_markup=types.ReplyKeyboardRemove())
    res = await leo_set_like(from_uid, to_uid, msg)
    if not res:
        await message.answer(i18n.gettext("Не удалось поставить лайк"))
    await next(message, state)

@router.callback_query(LeomatchProfileAction.filter(LeomatchProfiles.LOOCK))
async def choose_percent(query: types.CallbackQuery, state: FSMContext, callback_data: LeomatchProfileAction):
    await state.update_data(me=query.from_user.id)
    if callback_data.action == ProfileActionEnum.LIKE:
        await like(query.message, state, query.from_user.id, callback_data.user_id)
    elif callback_data.action == ProfileActionEnum.MESSAGE:
        await query.message.answer(
            i18n.gettext("Введите сообщение или отправьте видео (макс 15 сек)"),
            reply_markup=cancel()
        )
        await state.update_data(selected_id=callback_data.user_id)
        await state.set_state(LeomatchProfiles.INPUT_MESSAGE)
    elif callback_data.action == ProfileActionEnum.REPORT:
        await query.message.delete()
        await query.message.answer(
            i18n.gettext("Вы точно хотите подать жалобу? Учтите, если жалоба будет необоснованной, то вы сами можете быть забанены"),
            reply_markup=profile_alert(query.from_user.id, callback_data.user_id)
        )
    elif callback_data.action == ProfileActionEnum.SLEEP:
        pass
    elif callback_data.action == ProfileActionEnum.DISLIKE:
        await next(query.message, state)

@router.message(F.text == __("Отменить"), LeomatchProfiles.INPUT_MESSAGE)
async def cancel_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    leos = data.get("leos", [])
    leos.insert(0, data.get("selected_id"))
    await state.update_data(selected_id=None, leos=leos)
    await message.answer(i18n.gettext("Отменено"), reply_markup=types.ReplyKeyboardRemove())
    await next(message, state)

@router.message(LeomatchProfiles.INPUT_MESSAGE)
async def send_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_id = data.get("selected_id")
    await state.update_data(selected_id=None)
    await state.set_state("*")
    msg = None
    if message.text:
        msg = message.text
    elif message.video_note:
        msg = message.video_note.file_id
    else:
        await message.answer(i18n.gettext("Пожалуйста, напишите текст или отправьте видео"))
        return
    await like(message, state, message.from_user.id, selected_id, msg)

@router.message(F.text == __("Да"), LeomatchProfiles.MANAGE_LIKES)
async def view_likes(message: types.Message, state: FSMContext):
    await message.answer(i18n.gettext("Вот аккаунты, кому Вы понравились:"), reply_markup=types.ReplyKeyboardRemove())
    await next_like(message, state)

@router.message(F.text == __("Нет"), LeomatchProfiles.MANAGE_LIKES)
async def clear_likes(message: types.Message):
    await message.answer(i18n.gettext("Все лайки удалены"), reply_markup=types.ReplyKeyboardRemove())
    await clear_all_likes(message.from_user.id)

@router.callback_query(LeomatchLikeAction.filter(LeomatchProfiles.MANAGE_LIKE))
async def manage_like(query: types.CallbackQuery, state: FSMContext, callback_data: LeomatchLikeAction):
    if callback_data.action == LikeActionEnum.LIKE:
        leo = await get_leo(callback_data.user_id)
        link = ""
        client = await leo.user
        is_username = False
        if client.username:
            link = client.username
            is_username = True
        else:
            link = client.uid
        try:
            await bot_show_profile_db(callback_data.user_id, query.from_user.id)
        except Exception:
            await next_like(query.message, state)
        try:
            await query.message.answer(
                i18n.gettext("Начинай общаться!"),
                reply_markup=write_profile(link, is_username)
            )
        except Exception:
            await query.message.answer(
                i18n.gettext("Извините, Вы не сможете начать общение, так как у пользователя приватный аккаунт")
            )
    elif callback_data.action == LikeActionEnum.REPORT:
        pass
    await state.update_data(me=query.from_user.id)
    await delete_like(callback_data.user_id, query.from_user.id)
    await next_like(query.message, state)

# @router.callback_query(LeomatchProfileAlert.filter(F.state(LeomatchProfiles.LOOCK)))
# async def report_profile(query: types.CallbackQuery, state: FSMContext, callback_data: LeomatchProfileAlert):
#     if callback_data.action == "yes":
#         sender = await get_leo(callback_data.sender_id)
#         account = await get_leo(callback_data.account_id)
#         sender_user = await sender.user
#         account_user = await account.user
#         await show_media(bot, ADMIN_ID, callback_data.account_id)
#         await bot.send_message(
#             chat_id=ADMIN_ID,
#             text=i18n.gettext(
#                 "Пользователь: @{sender_user} ({sender_user_id}) пожаловался на \n"
#                 "Пользователя: @{account_user} ({account_user_id})\n"
#             ).format(
#                 sender_user=sender_user.full_name,
#                 sender_user_id=sender_user.id,
#                 account_user=account_user.full_name,
#                 account_user_id=account_user.id
#             ),
#             reply_markup=profile_alert_action(callback_data.sender_id, callback_data.account_id)
#         )
#         await query.message.edit_text(i18n.gettext("Жалоба отправлена"))
#     await state.update_data(me=query.from_user.id)
#     await next(query.message, state)
