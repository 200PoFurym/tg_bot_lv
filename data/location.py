import math
import random
import string
from aiogram import types, Router, F
from tortoise.queryset import Q
from main import i18n
from models import User, ReferralCode
from datetime import datetime, timezone, timedelta

router = Router()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

max_views = 100


async def has_valid_views(user: User) -> bool:
    now = datetime.now(timezone.utc)
    if user.views_expiry_date is None or user.views_expiry_date <= now:
        user.daily_profile_views = 100
        user.views_expiry_date = now + timedelta(days=1)
        await user.save()

    if user.daily_profile_views > 0:
        user.daily_profile_views -= 1
        await user.save()
        return True

    return False

async def find_nearby_users(user: User, max_distance=10):
    min_age = user.min_age
    max_age = user.max_age
    preferred_sex = user.which_search
    filtered_users = await User.filter(
        Q(age__gte=min_age) & Q(age__lte=max_age) & Q(sex=preferred_sex) & Q(latitude__isnull=False) & Q(longitude__isnull=False)
    ).exclude(user_id=user.user_id).all()

    nearby_users = []
    for i in filtered_users:
        distance = haversine(user.latitude, user.longitude, i.latitude, i.longitude)
        if distance <= max_distance:
            nearby_users.append((i, distance))

    nearby_users.sort(key=lambda x: x[1])

    return nearby_users

@router.message(F.text == i18n.gettext("Найти поблизости"))
async def nearby_users(message: types.Message):
    user_id = message.from_user.id
    user = await User.get_or_none(user_id=user_id)
    if not user:
        await message.reply(i18n.gettext("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь сначала."))
        return

    if not await has_valid_views(user):
        await message.reply(i18n.gettext("Вы исчерпали лимит на просмотр профилей или срок действия ваших просмотров истек. Поделитесь своим реферальным кодом, чтобы получить дополнительные просмотры."))
        return

    nearby = await find_nearby_users(user, max_distance=100)
    if nearby:
        for u in nearby:
            await message.reply(i18n.gettext(f'Найден: {u[0].full_name}, возраст: {u[0].age}, локация: {u[0].address}'))
    else:
        await message.reply(i18n.gettext("Поблизости никого нет."))



@router.message(F.text == i18n.gettext("Получить реферальный код"))
async def referral(message: types.Message):
    user_id = message.from_user.id
    user = await User.get_or_none(user_id=user_id)

    if not user:
        await message.reply(i18n.gettext("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь сначала."))
        return

    referral_link = await create_referral_code_for_user(user_id)
    await message.reply(f"Ваш реферальный код: {referral_link}")

async def like_user(user_id: int):
    user = await User.get(user_id=user_id)
    user.likes += 1
    await user.save()

async def get_top_users(sex: str, limit: int = 100):
    return await User.filter(sex=sex).order_by('-likes').limit(limit)

@router.message(F.text == i18n.gettext("Топ 100 девушек"))
async def top_girls(message: types.Message):
    top_girls = await get_top_users(sex="FEMALE", limit=100)
    if top_girls:
        response = i18n.gettext("\n".join([f'{i+1}. {user.full_name} - {user.likes} лайков' for i, user in enumerate(top_girls)]))
        await message.reply(response)
    else:
        await message.reply(i18n.gettext("Нет данных для отображения."))

@router.message(F.text == i18n.gettext("Топ 100 парней"))
async def top_boys(message: types.Message):
    top_boys = await get_top_users(sex="MALE", limit=100)
    if top_boys:
        response = i18n.gettext("\n".join([f'{i+1}. {user.full_name} - {user.likes} лайков' for i, user in enumerate(top_boys)]))
        await message.reply(response)
    else:
        await message.reply(i18n.gettext("Нет данных для отображения."))



def generate_referral_code(length=16):
    try:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        print(f"Generated referral code: {code}")
        return code
    except Exception as e:
        print(f"Error generating referral code: {e}")
        raise

async def generate_unique_referral_code():
    while True:
        code = generate_referral_code()
        if not await ReferralCode.exists(code=code):
            return code


async def save_referral_code(user_id: int):
    user = await User.get_or_none(user_id=user_id)

    if user is None:
        print(f"User with id {user_id} does not exist.")
        return None

    if user.referral_code:
        print(f"User with id {user_id} already has a referral code.")
        return user.referral_code

    code = await generate_unique_referral_code()
    user.referral_code = code
    await user.save()
    return code


def generate_referral_link(referral_code: str) -> str:
    base_url = "https://t.me/your_bot_username"
    return f"{base_url}?start={referral_code}"


async def create_referral_code_for_user(user_id: int):
    code = await save_referral_code(user_id)
    if code:
        referral_link = generate_referral_link(code)
        print(f"Generated referral link: {referral_link}")
        return referral_link
    else:
        print("Failed to generate referral code.")
        return None