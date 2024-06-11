import asyncio
import pickle

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app import settings
from db import models
from db.main import sessionmanager
from app.main import redis
from bot import keyboards


async def command_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    tasks = []
    user_id = update.effective_user.id
    msg = "Привет! Отправь мне геопозицию и я подскажу удаленность интересующих тебя объектов."
    if not (
        user_bytes := await redis.hget(
            user_id, "profile"
        )
    ):
        async with (
            sessionmanager.session() as session
        ):
            if not (
                user_profile := await models.Profile.get_by_telegram_id(
                    session,
                    user_id,
                )
            ):
                await models.Profile.create(
                    session,
                    user_telegram_id=user_id,
                    is_admin=False,
                )
                await models.Preferences.create(
                    session,
                    user_telegram_id=user_id,
                )
                user_profile = await models.Profile.get_by_telegram_id(
                    session,
                    user_id,
                )
                await redis.hset(
                    user_id,
                    "profile",
                    pickle.dumps(user_profile),
                )
    else:
        user_profile = pickle.loads(user_bytes)
    is_phone_confirmed = (
        user_profile.is_phone_confirmed
    )

    keyboard = (
        await keyboards.get_start_keyboard()
    )

    tasks.extend(
        [
            update.message.reply_text(
                msg,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            ),
            redis.hset(
                user_id, "current_state", "start"
            ),
        ]
    )

    await asyncio.gather(*tasks)


async def command_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    async with (
        sessionmanager.session() as session
    ):
        user_profile = await models.Profile.get_by_telegram_id(
            session,
            user_id,
            joined=True,
        )
        await redis.hset(
            user_id,
            "profile",
            pickle.dumps(user_profile),
        )
    msg = await generators.generate_profile_card(
        user_profile,
    )
    await update.message.reply_text(msg)


async def command_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
): ...
