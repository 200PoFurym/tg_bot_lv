# from aiogram import types
# from keyboards import reply_kb
# from models import LeomatchRegistration, LeomatchMain
# from aiogram.fsm.context import FSMContext
#
# from main import i18n
# from shortcuts import get_leo
#
#
#
# async def manage(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     me = data.get("me") if data.get("me") else message.from_user.id
#     leo = await get_leo(me)
#     text = ""
#     if not leo.active or not leo.search:
#         count = 2
#         text = i18n.gettext(
#             "\nСейчас аккаунт выключен от поиска, если Вы начнете просматривать аккаунты, то Ваш аккаунт вновь включится для поиска другим пользователем")
#     else:
#         count = 3
#         text = i18n.gettext("\n3. Больше не ищу")
#     await message.answer(i18n.gettext("1. Просмотр профилей.\n2. Мой профиль.{text}").format(text=text),
#                          reply_markup=reply_kb.get_numbers(count, True))
#     await state.set_state(LeomatchMain.WAIT)
#
#
# async def set_sex(sex: str, message: types.Message, state: FSMContext):
#     await state.update_data(sex=sex)
#     await message.answer(i18n.gettext("Кого Вы ищите?"), reply_markup=reply_kb.which_search())
#     await state.set_state(LeomatchRegistration.WHICH_SEARCH)
#
#
# async def set_which_search(which_search: str, message: types.Message, state: FSMContext):
#     await state.update_data(which_search=which_search)
#     await message.answer(i18n.gettext("Из какого ты города?"), reply_markup=reply_kb.remove())
#     await state.set_state(LeomatchRegistration.CITY)
#
#
# async def begin_registration(message: types.Message, state: FSMContext):
#     await state.clear()
#     await message.answer(i18n.gettext("Сколько тебе лет?"), reply_markup=reply_kb.cancel())
#     await state.set_state(LeomatchRegistration.AGE)
