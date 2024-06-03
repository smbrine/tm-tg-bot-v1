import asyncio
import json

import grpc
import telegram.constants
from telegram import (
    Update,
)
from telegram.ext import ContextTypes

from db import models
from db.main import sessionmanager
from bot.main import pb
from bot import generators

async def create_distance_tasks(location, objects):
    tasks = []
    for obj in objects:
        task = pb.CalculateDistance(
            location.latitude,
            location.longitude,
            obj["name"],
            obj["search_distance"]
        )
        tasks.append(task)
    return await asyncio.gather(*tasks)

async def generate_distance_cards(results, objects):
    msg = ""
    for result, obj in zip(results, objects):
        msg += await generators.generate_distance_card(
            result.is_found,
            obj["name"],
            result.distance,
            json.loads(result.object),
            obj["search_distance"]
        ) + '\n\n'
    return msg

async def message_location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    async with (
        sessionmanager.session() as session
    ):
        user_profile = await models.Profile.get_by_telegram_id(
            session, update.effective_user.id
        )
        await user_profile.increment_general_requests(
            session
        )
    objects = [
        {
            "name": "school",
            "search_distance": 10000
        },
        {
            "name": "subway",
            "search_distance": 10000
        },
        {
            "name": "supermarket",
            "search_distance": 10000
        },
        {
            "name": "kindergarten",
            "search_distance": 10000
        },
        {
            "name": "parking",
            "search_distance": 10000
        },
    ]

    results = await create_distance_tasks(update.message.location, objects)
    message = await generate_distance_cards(results, objects)

    # closest_school, closest_subway = (await
    #     asyncio.gather(
    #         pb.CalculateDistance(
    #             update.message.location.latitude,
    #             update.message.location.longitude,
    #             "school",
    #             1000,
    #         ),
    #         pb.CalculateDistance(
    #             update.message.location.latitude,
    #             update.message.location.longitude,
    #             "subway",
    #             1000,
    #         ),
    #     )
    # )
    # msg = "Вот что я нашел в указанном месте:\n\n"
    # msg += await generators.generate_distance_card(
    #     closest_school.is_found,
    #     "school",
    #     round(closest_school.distance, 0),
    #     json.loads(closest_school.object),
    #     1000
    # )
    # msg += "\n\n"
    # msg += await generators.generate_distance_card(
    #     closest_subway.is_found,
    #     "subway",
    #     round(closest_subway.distance, 0),
    #     json.loads(closest_subway.object),
    #     1000
    # )
    await update.message.reply_text(message, parse_mode=telegram.constants.ParseMode.HTML)
