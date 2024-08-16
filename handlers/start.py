from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.registration import return_main
from keyboards import reply_kb
from keyboards.reply_kb import main_menu_kb
from main import logger, i18n
from shortcuts import exists_leo, get_leo
from models import LeoMatchModel, User, LeomatchMain
from models import LeomatchRegistration
from aiogram.utils.i18n import lazy_gettext as __

router = Router()

async def manage(message: types.Message, state: FSMContext):
    data = await state.get_data()
    me = data.get("me") if data.get("me") else message.from_user.id
    leo = await get_leo(me)
    text = ""
    if not leo.active or not leo.search:
        count = 2
        text = i18n.gettext(
            "\nСейчас аккаунт выключен от поиска, если Вы начнете просматривать аккаунты, то Ваш аккаунт вновь включится для поиска другим пользователем")
    else:
        count = 3
        text = i18n.gettext("\n3. Больше не ищу")
    await message.answer(
        i18n.gettext("1. Просмотр профилей.\n2. Мой профиль.{text}").format(text=text),
        reply_markup=reply_kb.get_numbers(count, True)
    )
    await state.set_state(LeomatchMain.WAIT)



@router.message(F.text == __("🫰 Знакомства"))
async def bot_start(message: types.Message, state: FSMContext):
    has_user = await exists_leo(message.from_user.id)
    if not has_user:
        await message.answer(
            i18n.gettext("Добро пожаловать! Я - бот для знакомств. Я помогу тебе найти свою вторую половинку."),
            reply_markup=reply_kb.begin_registration()
        )
        await state.set_state(LeomatchRegistration.START)
    else:
        account: LeoMatchModel = await get_leo(message.from_user.id)
        if account.blocked:
            await message.answer(i18n.gettext("Ваш аккаунт заблокирован"))
            return
        await manage(message, state)
        kbrds = InlineKeyboardBuilder()
        kbrds.add(
            types.InlineKeyboardButton(
                text=i18n.gettext("Запустите WebApp"),
                web_app=types.WebAppInfo(url='https://dosimple.io/waleo/')
            )
        )
        await message.answer(
            i18n.gettext("Попробуйте наш WebAPP знакомства"),
            reply_markup=kbrds.as_markup()
        )

@router.message(F.text == __("Я не хочу никого искать"))
async def cancel_search(message: types.Message, state: FSMContext):
    await return_main(message, state)
