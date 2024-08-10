from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import i18n
from models import User

router = Router()

AVAILABLE_LANGUAGES = {
    'en': 'English',
    'ru': 'Русский',
    'uz': 'O‘zbekcha',
    'es': 'Español'
}

@router.message(Command(commands=['set_language']))
async def set_language(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    for lang_code, lang_name in AVAILABLE_LANGUAGES.items():
        keyboard.add(InlineKeyboardButton(text=lang_name, callback_data=f'set_lang_{lang_code}'))

    await message.reply(i18n.gettext("Выберите язык / Select a language:"), reply_markup=keyboard)

async def save_user_language(user_id, lang_code):
    user, created = await User.get_or_create(user_id=user_id)
    user.language_code = lang_code
    await user.save()

@router.callback_query(F.data.startswith('set_lang_'))
async def change_language(callback_query: types.CallbackQuery):
    lang_code = callback_query.data.split('_')[2]

    if lang_code in AVAILABLE_LANGUAGES:
        user_id = callback_query.from_user.id
        await save_user_language(user_id, lang_code)

        i18n.ctx_locale.set(lang_code)

        await callback_query.answer()
        await callback_query.message.answer(i18n.gettext(f"Язык изменен на {AVAILABLE_LANGUAGES[lang_code]}"))
    else:
        await callback_query.answer(i18n.gettext("Этот язык не поддерживается."))
