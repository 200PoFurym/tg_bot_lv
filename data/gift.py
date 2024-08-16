from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import i18n, bot
from models import User, Gift
import logging



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = Router()

GIFT_MEDIA = {
    i18n.gettext('flowers'): 'https://i.pinimg.com/originals/16/ec/e0/16ece0f2ef8c779c0d59bb5cc828b2ab.gif',
    i18n.gettext('cake'): 'https://img1.picmix.com/output/pic/normal/3/3/4/5/4315433_74822.gif',
    i18n.gettext('bunny'): 'https://img1.picmix.com/output/pic/normal/6/5/0/8/5348056_0de86.gif',
    i18n.gettext('bear'): 'https://i.gifer.com/origin/6b/6bd93ac23bbba8d3a09e0679b89fe843_w200.gif',
    i18n.gettext('rocket'): 'https://i.gifer.com/origin/0f/0f685243c5a5c76f4e45112d54a47f52_w200.gif'
}


import logging
logging.basicConfig(level=logging.INFO)

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
class SearchStates(StatesGroup):
    waiting_for_search_name = State()

search_command = i18n.gettext("Найти пользователя").strip()


@router.message(F.text == search_command)
async def start_search(message: types.Message, state: FSMContext):
    logging.info(f"Received message: {message.text}")

    await state.set_state(SearchStates.waiting_for_search_name)
    await message.reply(i18n.gettext("Укажите имя пользователя для поиска"))


@router.message(SearchStates.waiting_for_search_name)
async def handle_name(message: types.Message, state: FSMContext):
    text_after_command = message.text.strip()

    logging.info(f"Text entered by user: '{text_after_command}'")

    if not text_after_command:
        await message.reply(i18n.gettext("Укажите имя пользователя для поиска"))
        return

    search_name = text_after_command.lower()
    sender_id = message.from_user.id

    logging.info(f"Extracted search name: '{search_name}'")

    try:
        found_users = await User.filter(full_name__icontains=search_name).exclude(id=sender_id).all()

        logging.info(f"Found users count: {len(found_users)}")

        if not found_users:
            await message.reply(i18n.gettext("Пользователь с таким именем не найден."))
            return

        for receiver in found_users:
            await view_profile(sender_id, receiver)

        logging.info("User profiles displayed successfully.")

    except Exception as e:
        await message.reply(i18n.gettext("Произошла ошибка при поиске пользователя. Пожалуйста, попробуйте позже."))
        logging.error(f"Error: {e}")

    await state.clear()


def create_keyboard(receiver_id: int) -> InlineKeyboardMarkup:
    send_gift_button = InlineKeyboardButton(text=i18n.gettext("Отправить подарок"), callback_data=f"{SEND_GIFT_PREFIX}|{receiver_id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[send_gift_button]])
    return keyboard


SEND_GIFT_PREFIX = i18n.gettext("Отправить подарок")
CHOOSE_GIFT_PREFIX = i18n.gettext("Выберите тип подарка:")

@router.callback_query(F.data.contains(SEND_GIFT_PREFIX))
async def process_callback_gift(callback_query: types.CallbackQuery):
    logging.info(f"Callback handler triggered with data: {callback_query.data}")
    try:
        data = callback_query.data.split('|')
        logging.info(f"Callback data: {data}")
        if len(data) < 2:
            await callback_query.answer(i18n.gettext("Неверный формат данных."))
            return
        action = data[0]
        user_id = int(data[1].strip())
        sender_id = callback_query.from_user.id

        users, error_message = await get_users(sender_id, user_id)
        if error_message:
            await callback_query.answer(error_message)
            return

        user_exists = await User.exists(user_id=user_id)
        if not user_exists:
            await callback_query.answer(i18n.gettext("Пользователь не найден."))
            return


        if action != SEND_GIFT_PREFIX:
            await callback_query.answer(i18n.gettext("Неверное действие."))
            return

        users, error_message = await get_users(sender_id, user_id)
        if error_message:
            await callback_query.answer(error_message)
            return

        _, receiver = users

        buttons = [
            InlineKeyboardButton(
                text=gift_type,
                callback_data=f"{CHOOSE_GIFT_PREFIX}|{receiver.user_id}|{gift_type}"
            )
            for gift_type in GIFT_MEDIA
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        logging.info(f"Generated keyboard: {keyboard}")

        await callback_query.message.answer(i18n.gettext("Выберите тип подарка:"), reply_markup=keyboard)

    except Exception as e:
        await callback_query.answer(i18n.gettext("Произошла ошибка при обработке запроса."))
        logging.error(f"Error processing gift callback: {e}")

async def send_gift_media(user_id: int, gift_type: str, media_url: str):
    try:
        logging.info(f"Sending gift '{gift_type}' to user {user_id} with media URL: {media_url}")
        if media_url.endswith('.gif'):
            await bot.send_animation(user_id, media_url,
                                     caption=i18n.gettext("Вам отправили {gift}").format(gift=gift_type))
        elif media_url.endswith('.mp4'):
            await bot.send_video(user_id, media_url,
                                 caption=i18n.gettext("Вам отправили {gift}").format(gift=gift_type))
        else:
            await bot.send_photo(user_id, media_url,
                                 caption=i18n.gettext("Вам отправили {gift}").format(gift=gift_type))

        logging.info(f"Gift {gift_type} sent to user {user_id} with media URL: {media_url}")

    except Exception as e:
        await bot.send_message(user_id,
                               i18n.gettext("Произошла ошибка при отправке подарка. Пожалуйста, попробуйте позже."))
        logging.error(f"Error sending gift media: {e}")


async def get_users(sender_id: int, receiver_id: int):
    try:
        sender = await User.get_or_none(user_id=sender_id)
        receiver = await User.get_or_none(id=receiver_id)

        if not sender:
            logging.error(f"Sender with ID {sender_id} does not exist.")
            return None, i18n.gettext("Отправитель не найден.")

        if not receiver:
            logging.error(f"Receiver with ID {receiver_id} does not exist.")
            return None, i18n.gettext("Пользователь не найден.")

        if receiver.id == sender.id:
            return None, i18n.gettext("Вы не можете отправить подарок самому себе.")

        return (sender, receiver), None

    except Exception as e:
        logging.error(f"Error in get_users function: {e}")
        return None, i18n.gettext("Произошла ошибка при получении пользователей.")



@router.callback_query(F.data.startswith(CHOOSE_GIFT_PREFIX))
async def choose_gift_type(callback_query: types.CallbackQuery):
    logging.info(f"Callback handler triggered with data: {callback_query.data}")
    try:
        data = callback_query.data.split('|')
        if len(data) < 3:
            await callback_query.answer(i18n.gettext("Неверный формат данных."))
            return
        action = data[0]
        user_id = int(data[1])
        gift_type = data[2]
        sender_id = callback_query.from_user.id

        logging.info(f"Received action: {action}, user_id: {user_id}, gift_type: {gift_type}, sender_id: {sender_id}")

        if action != CHOOSE_GIFT_PREFIX:
            await callback_query.answer(i18n.gettext("Неверное действие."))
            return

        users, error_message = await get_users(sender_id, user_id)
        if error_message:
            await callback_query.answer(error_message)
            return

        _, receiver = users

        media_url = GIFT_MEDIA.get(gift_type)
        if not media_url:
            await callback_query.answer(i18n.gettext("Неверный тип подарка."))
            return

        await send_gift_media(receiver.user_id, gift_type, media_url)
        await Gift.create(sender_id=sender_id, receiver_id=receiver.user_id, type=gift_type, media_url=media_url)
        await callback_query.answer(i18n.gettext("Подарок успешно отправлен!"))
        await callback_query.message.answer(i18n.gettext("Вы отправили {gift} {receiver_name}!").format(
            gift=gift_type, receiver_name=receiver.full_name))

    except Exception as e:
        await callback_query.answer(i18n.gettext("Произошла ошибка при выборе подарка."))
        logging.error(f"Error choosing gift type: {e}")

async def view_profile(sender_id: int, receiver: User):
    try:
        profile_info = (
            f"{i18n.gettext('Имя')}: {receiver.full_name}\n"
            f"{i18n.gettext('Возраст')}: {receiver.age}\n"
            f"{i18n.gettext('Город')}: {receiver.city}\n"
            f"{i18n.gettext('Обо мне')}: {receiver.about_me}\n"
        )

        keyboard = create_keyboard(receiver.id)

        logging.info(f"Keyboard markup: {keyboard}")

        await bot.send_photo(sender_id, receiver.file_id, caption=profile_info, reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(sender_id, i18n.gettext("Произошла ошибка при просмотре профиля. Пожалуйста, попробуйте позже."))
        logging.error(f"Error in view_profile: {e}")


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
