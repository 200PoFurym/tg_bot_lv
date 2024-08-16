from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram import types
from main import i18n

def main_menu_kb():
    button_change_data = KeyboardButton(text=i18n.gettext("Изменить анкету"))
    button_get_referral = KeyboardButton(text=i18n.gettext("Получить реферальный код"))
    button_find_nearby = KeyboardButton(text=i18n.gettext("Найти поблизости"))
    button_top_girl = KeyboardButton(text=i18n.gettext("Топ 100 девушек"))
    button_top_men = KeyboardButton(text=i18n.gettext("Топ 100 парней"))
    button_send_gift = KeyboardButton(text=i18n.gettext("Найти пользователя"))
    button_profile = KeyboardButton(text=i18n.gettext("Профиль"))
    button_verify = KeyboardButton(text=i18n.gettext("Верификация"))
    button_my_gifts = KeyboardButton(text=i18n.gettext("Мои подарки"))

    reply_kb_main = ReplyKeyboardMarkup(
        keyboard=[
            [button_change_data, button_get_referral, button_find_nearby],
            [button_top_girl, button_top_men, button_send_gift],
            [button_profile, button_my_gifts, button_verify]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        type='reply'
    )
    return reply_kb_main

def begin_registration():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.gettext("Давай, начнем!"))],
            [KeyboardButton(text=i18n.gettext("Я не хочу никого искать"))]
        ],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard

def chooice_sex():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.gettext("Я парень"))],
            [KeyboardButton(text=i18n.gettext("Я девушка"))]
        ],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard

def final_registration():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.gettext("Да"))],
            [KeyboardButton(text=i18n.gettext("Изменить анкету"))]
        ],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard

def which_search():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.gettext("Девушку"))],
            [KeyboardButton(text=i18n.gettext("Парня"))],
            [KeyboardButton(text=i18n.gettext("Мне всё равно"))]
        ],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard

def cancel():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.gettext("Отменить"))]
        ],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard

def yes_no():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.gettext("Да"))],
            [KeyboardButton(text=i18n.gettext("Нет"))]
        ],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard

def get_numbers(count: int, add_exit: bool = False):
    buttons = [KeyboardButton(text=f"{x + 1}") for x in range(count)]
    if add_exit:
        buttons.append(KeyboardButton(text=i18n.gettext("Выйти")))
    keyboard = ReplyKeyboardMarkup(
        keyboard=[buttons],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard

def remove():
    return ReplyKeyboardRemove()

def save_current():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.gettext("Оставить текущее"))]
        ],
        resize_keyboard=True,
        type='reply'
    )
    return keyboard
