from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import i18n, bot
from models import User, Gift

router = Router()

GIFT_MEDIA = {
    i18n.gettext('flowers'): 'https://i.pinimg.com/originals/16/ec/e0/16ece0f2ef8c779c0d59bb5cc828b2ab.gif',
    i18n.gettext('cake'): 'https://img1.picmix.com/output/pic/normal/3/3/4/5/4315433_74822.gif',
    i18n.gettext('bunny'): 'https://img1.picmix.com/output/pic/normal/6/5/0/8/5348056_0de86.gif',
    i18n.gettext('bear'): 'https://i.gifer.com/origin/6b/6bd93ac23bbba8d3a09e0679b89fe843_w200.gif',
    i18n.gettext('rocket'): 'https://i.gifer.com/origin/0f/0f685243c5a5c76f4e45112d54a47f52_w200.gif'
}

@router.message(F.text.startswith(i18n.gettext("Найти пользователя")))
async def search_user(message: types.Message):
    args = message.text.split(' ', 1)
    if len(args) < 2:
        await message.reply(i18n.gettext("Укажите имя пользователя для поиска"))
        return

    search_name = args[1].strip().lower()
    sender_id = message.from_user.id

    try:
        found_users = await User.filter(full_name__icontains=search_name).exclude(id=sender_id).all()

        if not found_users:
            await message.reply(i18n.gettext("Пользователь с таким именем не найден."))
            return

        for receiver in found_users:
            await view_profile(sender_id, receiver)

    except Exception as e:
        await message.reply(i18n.gettext("Произошла ошибка при поиске пользователя. Пожалуйста, попробуйте позже."))
        print(f"Error: {e}")

async def send_gift_media(user_id: int, gift_type: str, media_url: str):
    try:
        if media_url.endswith('.gif'):
            await bot.send_animation(user_id, media_url, caption=i18n.gettext("Вам отправили {gift}").format(gift=gift_type))
        elif media_url.endswith('.mp4'):
            await bot.send_video(user_id, media_url, caption=i18n.gettext("Вам отправили {gift}").format(gift=gift_type))
        else:
            await bot.send_photo(user_id, media_url, caption=i18n.gettext("Вам отправили {gift}").format(gift=gift_type))
    except Exception as e:
        await bot.send_message(user_id, i18n.gettext("Произошла ошибка при отправке подарка. Пожалуйста, попробуйте позже."))
        print(f"Error sending gift media: {e}")

@router.callback_query(F.data.startswith("send_gift_"))
async def process_callback_gift(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split("_")[2])
    sender_id = callback_query.from_user.id

    try:
        sender = await User.get(id=sender_id)
        receiver = await User.get_or_none(id=user_id)

        if not receiver:
            await callback_query.answer(i18n.gettext("Пользователь не найден."))
            return

        if receiver.id == sender.id:
            await callback_query.answer(i18n.gettext("Вы не можете отправить подарок самому себе."))
            return

        keyboard = InlineKeyboardMarkup()
        for gift_type, gift_name in GIFT_MEDIA.items():
            button = InlineKeyboardButton(text=gift_name, callback_data=f"choose_gift_{receiver.id}_{gift_type}")
            keyboard.add(button)
        await callback_query.message.answer(i18n.gettext("Выберите тип подарка:"), reply_markup=keyboard)
    except Exception as e:
        await callback_query.answer(i18n.gettext("Произошла ошибка при обработке запроса."))
        print(f"Error processing gift callback: {e}")

@router.callback_query(F.data.startswith("choose_gift_"))
async def choose_gift_type(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    user_id, gift_type = int(data[2]), data[3]
    sender_id = callback_query.from_user.id

    try:
        sender = await User.get(id=sender_id)
        receiver = await User.get_or_none(id=user_id)

        if not receiver:
            await callback_query.answer(i18n.gettext("Пользователь не найден."))
            return

        if receiver.id == sender.id:
            await callback_query.answer(i18n.gettext("Вы не можете отправить подарок самому себе."))
            return

        media_url = GIFT_MEDIA.get(gift_type)
        if not media_url:
            await callback_query.answer(i18n.gettext("Неверный тип подарка."))
            return

        await Gift.create(sender_id=sender.id, receiver_id=receiver.id, type=gift_type, media_url=media_url)

        await send_gift_media(receiver.id, gift_type, media_url)

        await callback_query.answer(i18n.gettext("Подарок успешно отправлен!"))
        await callback_query.message.answer(i18n.gettext("Вы отправили {gift} {receiver_name}!").format(
            gift=gift_type, receiver_name=receiver.full_name))
    except Exception as e:
        await callback_query.answer(i18n.gettext("Произошла ошибка при выборе подарка."))
        print(f"Error choosing gift type: {e}")

async def view_profile(sender_id: int, receiver: User):
    try:
        profile_info = (
            f"{i18n.gettext('Фото')}: {receiver.photo_url}\n"
            f"{i18n.gettext('Имя')}: {receiver.full_name}\n"
            f"{i18n.gettext('Возраст')}: {receiver.age}\n"
            f"{i18n.gettext('Город')}: {receiver.city}\n"
            f"{i18n.gettext('Обо мне')}: {receiver.about_me}\n"
        )

        keyboard = InlineKeyboardMarkup()
        if sender_id != receiver.id:
            for gift_type, gift_name in GIFT_MEDIA.items():
                button = InlineKeyboardButton(text=f"{i18n.gettext('Отправить')} {gift_name}", callback_data=f"send_gift_{receiver.id}_{gift_type}")
                keyboard.add(button)

        await bot.send_message(sender_id, profile_info, reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(sender_id, i18n.gettext("Произошла ошибка при просмотре профиля. Пожалуйста, попробуйте позже."))
        print(f"Error in view_profile: {e}")

@router.message(F.text.startswith(i18n.gettext("Мои подарки")))
async def show_gifts(message: types.Message):
    user_id = message.from_user.id
    gifts = await Gift.filter(receiver_id=user_id).all()
    if not gifts:
        await message.reply(i18n.gettext("Вы не получали подарков."))
        return

    for gift in gifts:
        sender = await User.get(id=gift.sender_id)
        await bot.send_message(
            user_id,
            i18n.gettext("Подарок от {sender_name}\nТип: {gift_type}\nДата: {date_sent}\nМедиа: {media_url}").format(
                sender_name=sender.full_name,
                gift_type=gift.type,
                date_sent=gift.date_sent.strftime('%Y-%m-%d %H:%M'),
                media_url=gift.media_url
            )
        )
