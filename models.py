from aiogram import types, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from enum import Enum
import logging
import random
import string

router = Router()

class LeomatchRegistration(StatesGroup):
    START = State()
    AGE = State()
    MIN_AGE = State()
    MAX_AGE = State()
    CITY = State()
    ADDRESS = State()
    FULL_NAME = State()
    SEX = State()
    WHICH_SEARCH = State()
    ABOUT_ME = State()
    SEND_PHOTO = State()
    FINAL = State()

class LeomatchMain(StatesGroup):
    WAIT = State()
    PROFILES = State()
    MY_PROFILE = State()
    PROFILE_MANAGE = State()
    SLEEP = State()
    SET_DESCRIPTION = State()
    SET_PHOTO = State()

class LeomatchProfiles(StatesGroup):
    LOOCK = State()
    INPUT_MESSAGE = State()
    MANAGE_LIKES = State()
    MANAGE_LIKE = State()

class User(models.Model):
    id = fields.IntField(pk=True, unique=True)
    user_id = fields.IntField(unique=True)
    full_name = fields.CharField(max_length=50, unique=True)
    city = fields.CharField(max_length=50)
    age = fields.IntField()
    min_age = fields.IntField()
    max_age = fields.IntField()
    sex = fields.CharField(max_length=10)
    which_search = fields.CharField(max_length=10)
    about_me = fields.TextField()
    latitude = fields.FloatField()
    longitude = fields.FloatField()
    address = fields.TextField()
    media_type = fields.CharField(max_length=50)
    file_id = fields.CharField(max_length=255, null=True)
    file_url = fields.CharField(max_length=255)
    is_verified = fields.BooleanField(default=False)
    is_registered = fields.BooleanField(default=False)
    reference_face_encoding = fields.JSONField(null=True)
    profile_views = fields.IntField(default=0)
    daily_profile_views = fields.IntField(default=100)
    last_view_reset = fields.DatetimeField(auto_now_add=True)
    referral_code = fields.CharField(max_length=16, null=True, unique=True)
    referrals_count = fields.IntField(default=0)
    views_expiry_date = fields.DatetimeField(null=True)
    likes = fields.IntField(default=0)
    language_code = fields.CharField(max_length=2, default='ru')

    class Meta:
        table = "users"

class Gift(models.Model):
    id = fields.IntField(pk=True)
    sender_id = fields.ForeignKeyField('data.User', related_name='sent_gifts')
    receiver_id = fields.ForeignKeyField('data.User', related_name='received_gifts')
    type = fields.CharField(max_length=50)
    description = fields.CharField(max_length=200, null=True)
    media_url = fields.TextField(null=True)
    message = fields.TextField(null=True)
    date_sent = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "gifts"



class ReferralCode(models.Model):
    code = fields.CharField(max_length=255, unique=True)
    user = fields.ForeignKeyField('data.User', related_name="referral_codes", on_delete=fields.CASCADE)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "referral_codes"

class LeomatchChange(StatesGroup):
    CHANGE_NAME = State()
    CHANGE_AGE = State()
    CHANGE_MIN_AGE = State()
    CHANGE_MAX_AGE = State()
    CHANGE_CITY = State()
    CHANGE_ADDRESS = State()
    CHANGE_SEARCH = State()
    CHANGE_ABOUT_ME = State()
    CHANGE_PHOTO = State()

class SexEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    ANY = "any"

class MediaTypeEnum(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    VIDEO_NOTE = "video_note"

class LeoMatchModel(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("data.User", related_name="leo_matches")
    file_url = fields.CharField(max_length=255)
    media_type = fields.CharEnumField(MediaTypeEnum)
    sex = fields.CharEnumField(SexEnum)
    age = fields.IntField()
    full_name = fields.CharField(max_length=100)
    about_me = fields.TextField()
    city = fields.CharField(max_length=100)
    which_search = fields.CharEnumField(SexEnum)
    bot_username = fields.CharField(max_length=50)
    search = fields.BooleanField(default=True)
    active = fields.BooleanField(default=True)
    blocked = fields.BooleanField(default=False)

    class Meta:
        table = "leo_matches"

class LeoMatchLikesBasketModel(models.Model):
    id = fields.IntField(pk=True)
    from_user = fields.ForeignKeyField("data.LeoMatchModel", related_name="likes_given")
    to_user = fields.ForeignKeyField("data.LeoMatchModel", related_name="likes_received")
    message = fields.TextField(null=True)
    done = fields.BooleanField(default=False)

    class Meta:
        table = "leo_match_likes_basket"

User_Pydantic = pydantic_model_creator(User, name="User")
LeoMatchModel_Pydantic = pydantic_model_creator(LeoMatchModel, name="LeoMatch")
LeoMatchLikesBasketModel_Pydantic = pydantic_model_creator(LeoMatchLikesBasketModel, name="LeoMatchLikesBasket")
