from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tortoise.queryset import Q
from models import User
from main import bot, i18n
from data.gift import GIFT_MEDIA

router = Router()

@router.message(F.text.startswith(i18n.gettext("Найти пользователя")))
async def search_user(message: types.Message):
    args = message.text.split(maxsplit=1)[1].strip()
    if not args:
        await message.reply(i18n.gettext("Укажите имя пользователя для поиска."))
        return

    search_name = args.lower()
    found_users = await User.filter(full_name__icontains=search_name).all()

    if not found_users:
        await message.reply(i18n.gettext("Пользователи с таким именем не найдены."))
        return

    for user in found_users:
        await view_profile(message.from_user.id, user)

async def recommend_users(user: User):
    min_age = user.min_age
    max_age = user.max_age
    preferred_sex = user.which_search

    try:
        recommended_users = await User.filter(
            Q(age__gte=min_age, age__lte=max_age) &
            Q(sex=preferred_sex) &
            Q(latitude__isnull=False) &
            Q(longitude__isnull=False)
        ).exclude(id=user.id).all()

        if not recommended_users:
            await bot.send_message(user.user_id, i18n.gettext("Нет пользователей, соответствующих вашим критериям."))
            return

        for recommended_user in recommended_users:
            await view_profile(user.user_id, recommended_user)

    except Exception as e:
        await bot.send_message(user.user_id, i18n.gettext("Произошла ошибка при получении рекомендаций. Пожалуйста, попробуйте позже."))
        print(f"Error: {e}")

async def view_profile(user_id: int, viewed_user: User):
    try:
        user = await User.get(user_id=user_id)
        profile_info = (
            f"{i18n.gettext('Фото')}: {viewed_user.photo_url}\n"
            f"{i18n.gettext('Имя')}: {viewed_user.full_name}\n"
            f"{i18n.gettext('Возраст')}: {viewed_user.age}\n"
            f"{i18n.gettext('Город')}: {viewed_user.city}\n"
            f"{i18n.gettext('Обо мне')}: {viewed_user.about_me}\n"
        )

        keyboard = InlineKeyboardMarkup()
        if user.id != viewed_user.id:
            for gift_type, gift_name in GIFT_MEDIA.items():
                button = InlineKeyboardButton(
                    text=f"{i18n.gettext('Отправить')} {gift_name}",
                    callback_data=f"send_gift_{viewed_user.id}_{gift_type}"
                )
                keyboard.add(button)

        await bot.send_message(user_id, profile_info, reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(user_id, i18n.gettext("Произошла ошибка при отображении профиля. Пожалуйста, попробуйте позже."))
        print(f"Error: {e}")

async def recommend_users_periodically():
    try:
        users = await User.all()
        for user in users:
            await recommend_users(user)
    except Exception as e:
        print(f"Error: {e}")
