import contextvars
import logging

from aiogram import BaseMiddleware, types
from aiogram.types import Update
from aiogram.utils.i18n import I18n
from models import User

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

locale_var = contextvars.ContextVar('locale', default='ru')

class CustomI18nMiddleware(BaseMiddleware):
    def __init__(self, i18n: I18n):
        super().__init__()
        self.i18n = i18n
        self.logger = logging.getLogger(__name__)

    async def __call__(self, handler, event: Update, *args, **kwargs):
        locale = await self.get_locale(event)
        self.logger.debug(f"Setting locale to: {locale}")
        locale_var.set(locale)
        self.i18n.ctx_locale.set(locale)
        return await handler(event, *args, **kwargs)

    async def get_locale(self, event: Update) -> str:
        if event.message:
            user = event.message.from_user
            user_id = user.id

            db_user = await User.get_or_none(user_id=user_id)
            if db_user and db_user.language_code in ('en', 'ru', 'uz', 'es'):
                return db_user.language_code

            language_code = user.language_code
            logger.info(f"Received language code from user: {language_code}")

            if language_code in ('en', 'ru', 'uz', 'es'):
                return language_code

            logger.info(f"Language code {language_code} is not supported. Defaulting to 'ru'.")
        else:
            logger.info("No message found in the event. Defaulting to 'ru'.")
        return 'ru'

    async def on_process_message(self, message: types.Message, data: dict):
        logger.info("Setting i18n context")
        i18n = self.i18n
        i18n.ctx_locale.set('ru')
        data['i18n'] = i18n

def get_current_locale() -> str:
    current_locale = locale_var.get()
    logger.info(f"Current locale: {current_locale}")
    return current_locale