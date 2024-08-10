import math
from aiogram import types, Router, F
from tortoise.queryset import Q
from main import i18n
from models import User
from datetime import datetime, timedelta, timezone

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
    if user.views_expiry_date and user.views_expiry_date > datetime.now(timezone.utc):
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
            await message.reply(i18n.gettext(f'Найден: {u[0].name}, возраст: {u[0].age}, локация: {u[0].address}'))
    else:
        await message.reply(i18n.gettext("Поблизости никого нет."))

@router.message(F.text == i18n.gettext("Получить реферальный код"))
async def referral(message: types.Message):
    referral_n = message.get_args().strip().upper()
    user_id = message.from_user.id
    user = await User.get_or_none(user_id=user_id)
    if not user:
        await message.reply(i18n.gettext("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь сначала."))
        return

    referrer = await User.get_or_none(referral_code=referral_n)
    if referrer:
        user.profile_views += 20
        user.views_expiry_date = datetime.now(timezone.utc) + timedelta(days=1)
        referrer.referrals_count += 1
        await user.save()
        await referrer.save()
        await message.reply(i18n.gettext("Вы получили 20 дополнительных просмотров за использование реферального кода!"))
    else:
        await message.reply(i18n.gettext("Неверный реферальный код."))

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
        response = i18n.gettext("\n".join([f'{i+1}. {user.name} - {user.likes} лайков' for i, user in enumerate(top_girls)]))
        await message.reply(response)
    else:
        await message.reply(i18n.gettext("Нет данных для отображения."))

@router.message(F.text == i18n.gettext("Топ 100 парней"))
async def top_boys(message: types.Message):
    top_boys = await get_top_users(sex="MALE", limit=100)
    if top_boys:
        response = i18n.gettext("\n".join([f'{i+1}. {user.name} - {user.likes} лайков' for i, user in enumerate(top_boys)]))
        await message.reply(response)
    else:
        await message.reply(i18n.gettext("Нет данных для отображения."))
