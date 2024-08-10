from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.callback_datas import (
    LeomatchLikeAction, LeomatchProfileAction, LeomatchProfileAlert,
    LeomatchProfileBlock, LikeActionEnum, ProfileActionEnum
)
from main import i18n

def profile_view_action(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👍", callback_data=LeomatchProfileAction(action=ProfileActionEnum.LIKE, user_id=user_id).pack()),
        InlineKeyboardButton(text="💌", callback_data=LeomatchProfileAction(action=ProfileActionEnum.MESSAGE, user_id=user_id).pack()),
        InlineKeyboardButton(text="⚠️", callback_data=LeomatchProfileAction(action=ProfileActionEnum.REPORT, user_id=user_id).pack()),
        InlineKeyboardButton(text="👎", callback_data=LeomatchProfileAction(action=ProfileActionEnum.DISLIKE).pack())
    )
    return builder.as_markup()

def profile_like_action(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❤️", callback_data=LeomatchLikeAction(action=LikeActionEnum.LIKE, user_id=user_id).pack()),
        InlineKeyboardButton(text="👎", callback_data=LeomatchLikeAction(action=LikeActionEnum.DISLIKE, user_id=user_id).pack())
    )
    return builder.as_markup()

def profile_alert(sender_id: int, account_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=i18n.gettext("Да"), callback_data=LeomatchProfileAlert(action="yes", sender_id=sender_id, account_id=account_id).pack()),
        InlineKeyboardButton(text=i18n.gettext("Нет"), callback_data=LeomatchProfileAlert(action="no").pack())
    )
    return builder.as_markup()

def profile_alert_action(sender_id: int, account_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=i18n.gettext("Заблокировать"), callback_data=LeomatchProfileBlock(account_id=account_id).pack()),
        InlineKeyboardButton(text=i18n.gettext("Заблокировать отправителя"), callback_data=LeomatchProfileBlock(account_id=sender_id).pack()),
        InlineKeyboardButton(text=i18n.gettext("Отменить"), callback_data=LeomatchProfileBlock().pack())
    )
    return builder.as_markup()

def write_profile(username_or_uid: str, is_username: bool = False):
    builder = InlineKeyboardBuilder()
    link = f"https://t.me/{username_or_uid}" if is_username else f"tg://user?id={username_or_uid}"
    builder.row(
        InlineKeyboardButton(text=i18n.gettext("Написать"), url=link)
    )
    return builder.as_markup()
