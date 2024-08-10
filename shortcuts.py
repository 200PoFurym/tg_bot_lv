from dataclasses import dataclass
from aiogram import Bot, types
from aiogram.types import InputFile, ReplyKeyboardMarkup
from keyboards.inline_kb import write_profile
from tortoise.contrib.postgres.functions import Random
from models import LeoMatchLikesBasketModel, SexEnum, User, LeoMatchModel, MediaTypeEnum
from main import bot, i18n


async def get_client(uid: int):
    return await User.filter(uid=uid).first()

async def get_leo(uid: int):
    user = await get_client(uid)
    if user:
        leo = await LeoMatchModel.filter(user=user).first()
        return leo
    return None

async def search_leo(me: int):
    leo_me = await get_leo(me)
    kwargs = {}
    if leo_me.which_search != SexEnum.ANY:
        kwargs['sex'] = leo_me.which_search
    return await LeoMatchModel.filter(
        blocked=False,
        age__range=(leo_me.age-3, leo_me.age+3),
        search=True,
        active=True,
        **kwargs
    ).exclude(
        which_search__not_in=[leo_me.sex, SexEnum.ANY],
        id=leo_me.id
    ).annotate(order=Random()).order_by('order').limit(50)

async def get_leos_id(me: int):
    users_id = []
    leos = await search_leo(me)
    for leo in leos:
        users_id.append((await leo.user).uid)
    return users_id

async def exists_leo(uid: int):
    return await get_leo(uid) is not None

async def add_leo(uid: int, photo: str, media_type: str, sex: str, age: int, full_name: str, about_me: str, city: str, which_search: str, bot_username: str):
    client = await get_client(uid)
    format = "jpg" if media_type == "PHOTO" else "mp4"
    file_path = f"clientbot/data/leo/{uid}.{format}"
    await bot.download(file_path, photo)
    await LeoMatchModel.create(
        user=client,
        photo=file_path,
        media_type=media_type,
        sex=sex,
        age=age,
        full_name=full_name,
        about_me=about_me,
        city=city,
        which_search=which_search,
        bot_username=bot_username,
    )

async def update_leo(uid: int, photo: str, media_type: str, sex: str, age: int, full_name: str, about_me: str, city: str, which_search: str):
    leo = await get_leo(uid)
    format = "jpg" if media_type == "PHOTO" else "mp4"
    file_path = f"clientbot/data/leo/{uid}.{format}"
    await bot.download(file_path, photo)
    await leo.update_from_dict(
        {
            "photo": file_path,
            "media_type": media_type,
            "sex": sex,
            "age": age,
            "full_name": full_name,
            "about_me": about_me,
            "city": city,
            "which_search": which_search,
        }
    ).save()

async def show_media(bot: Bot, to_account: int, from_account: int, text_before: str = "", reply_markup: ReplyKeyboardMarkup = None):
    account: LeoMatchModel = await get_leo(from_account)
    account_user: User = await account.user
    account_id = account_user.id
    text = f"{text_before}\n{account.full_name} {account.age}, г {account.city}\n\n{account.about_me}"
    if account.media_type == MediaTypeEnum.VIDEO_NOTE:
        await bot.send_video_note(to_account, video_note=InputFile(f"clientbot/data/leo/{account_id}.mp4"), reply_markup=reply_markup)
        await bot.send_message(to_account, text=text)
    elif account.media_type == MediaTypeEnum.VIDEO:
        await bot.send_video(to_account, video=InputFile(f"clientbot/data/leo/{account_id}.mp4"), reply_markup=reply_markup)
        await bot.send_message(to_account, text=text)
    elif account.media_type == MediaTypeEnum.PHOTO:
        await bot.send_photo(to_account, photo=InputFile(f"clientbot/data/leo/{account_id}.jpg"), caption=text)
    else:
        await bot.send_message(to_account, text=text)

async def show_profile(message: types.Message, uid: int, full_name: str, age: int, city: str, about_me: str, url: str, media_type: str, keyboard: ReplyKeyboardMarkup = None, comment: str = None):
    text = f"\n\nВам сообщение: {comment}" if comment else ""
    caption = f"{full_name}, {age}, {city}\n{about_me}{text}"
    kwargs = {}
    if keyboard:
        kwargs['reply_markup'] = keyboard
    try:
        if media_type == "VIDEO":
            await message.answer_video(InputFile(f"clientbot/data/leo/{uid}.mp4"), caption=caption, **kwargs)
        else:
            await message.answer_photo(InputFile(f"clientbot/data/leo/{uid}.jpg"), caption=caption, **kwargs)
    except Exception as e:
        await message.answer(text=f"Ошибка: {e}")

async def bot_show_profile(to_uid: int, from_uid: int, full_name: str, age: int, city: str, about_me: str, url: str, media_type: str, username: str, keyboard: ReplyKeyboardMarkup = None):
    leo = await get_leo(to_uid)
    caption = f"{full_name}, {age}, {city}\n{about_me}"
    kwargs = {}
    if keyboard:
        kwargs['reply_markup'] = keyboard
    await bot.send_message(to_uid, "Есть взаимная симпатия!")
    if media_type == "PHOTO":
        await bot.send_photo(to_uid, InputFile(f"clientbot/data/leo/{from_uid}.jpg"), caption=caption, **kwargs)
    elif media_type == "VIDEO":
        await bot.send_video(to_uid, InputFile(f"clientbot/data/leo/{from_uid}.mp4"), caption=caption, **kwargs)

    link = username if username else from_uid
    try:
        await bot.send_message(to_uid, i18n.gettext("Начинай общаться!"), reply_markup=write_profile(link, bool(username)))
    except Exception:
        await bot.send_message(to_uid, i18n.gettext("Извините, Вы не сможете начать общение так как у пользователя приватный аккаунт"))

async def show_profile_db(message: types.Message, uid: int, keyboard: ReplyKeyboardMarkup = None, comment: str = None):
    leo = await get_leo(uid)
    await show_profile(message, uid, f'{leo.full_name}', leo.age, leo.city, leo.about_me, leo.photo, leo.media_type, keyboard=keyboard, comment=comment)

async def bot_show_profile_db(to_uid: int, uid: int, keyboard: ReplyKeyboardMarkup):
    leo = await get_leo(uid)
    user = await leo.user
    await bot_show_profile(to_uid, uid, f'{leo.full_name}', leo.age, leo.city, leo.about_me, leo.photo, leo.media_type, user.username, keyboard=keyboard)

async def update_profile(uid: int, kwargs: dict):
    leo = await get_leo(uid)
    await leo.update_from_dict(kwargs)
    await leo.save()

async def leo_set_like(from_uid: int, to_uid: int, message: str = None):
    from_user = await get_leo(from_uid)
    to_user = await get_leo(to_uid)
    if not from_user or not to_user:
        return False
    await LeoMatchLikesBasketModel.create(
        from_user=from_user,
        to_user=to_user,
        message=message,
    )
    return True

async def get_likes_count(uid: int):
    return await LeoMatchLikesBasketModel.filter(to_user=await get_leo(uid), done=False).count()

async def get_distinkt_likes():
    return await LeoMatchLikesBasketModel.filter(done=False).distinct()

async def get_first_like(uid: int):
    return await LeoMatchLikesBasketModel.filter(to_user=await get_leo(uid), done=False).first()

async def clear_all_likes(uid: int):
    return await LeoMatchLikesBasketModel.filter(to_user=await get_leo(uid)).update(done=True)

async def delete_like(from_uid: int, to_uid: int):
    await LeoMatchLikesBasketModel.filter(from_user=await get_leo(from_uid), to_user=await get_leo(to_uid)).update(done=True)

@dataclass
class Analitics:
    count_users: int
    count_man: int
    count_female: int


async def get_analitics(bot_username: str = None):
    kwargs = {}
    if bot_username:
        kwargs['bot_username'] = bot_username

    users_qs = LeoMatchModel.filter(**kwargs, active=True, search=True)

    total_count = await users_qs.count()

    man_count = await users_qs.filter(sex=SexEnum.MALE).count()
    female_count = await users_qs.filter(sex=SexEnum.FEMALE).count()

    return Analitics(total_count, man_count, female_count)
