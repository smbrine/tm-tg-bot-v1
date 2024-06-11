import asyncio
import io
import json

import grpc
import telegram.constants
from telegram import (
    Update,
)
from telegram.ext import ContextTypes

from app import settings
from db import models
from db.main import sessionmanager
from bot.main import pb, ms, dc
from bot import generators, schemas
import matplotlib.pyplot as plt

async def make_a_pie(x, y):
    labels = ['Жилая застройка', 'Нежилая застройка']
    sizes = [x, y]
    colors = ['yellow', 'grey']

    # Create the pie chart
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Соотношение застройки')

    # Save the pie chart to a byte buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

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
        ) + '\n'
    return msg

async def message_location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    async with (
        sessionmanager.session() as session
    ):
        user_id = update.effective_user.id
        user_profile = await models.Profile.get_by_telegram_id(
            session, user_id
        )
        await user_profile.increment_general_requests(
            session
        )
    objects = [
        {
            "name": "school",
            "search_distance": 1000
        },
        {
            "name": "subway",
            "search_distance": 1000
        },
        {
            "name": "supermarket",
            "search_distance": 500
        },
        {
            "name": "kindergarten",
            "search_distance": 500
        },
        {
            "name": "parking",
            "search_distance": 500
        },
    ]
    message = ''
    # results = await create_distance_tasks(update.message.location, objects)
    # message += await generate_distance_cards(results, objects)
    #
    # features = [
    #     schemas.Feature(
    #         name=str(json.loads(res.object)['tags']),
    #         type='Point',
    #         geometry=schemas.Geometry(
    #             points=[
    #                 schemas.Point(
    #                     latitude=json.loads(res.object).get('lat') or json.loads(res.object).get('center')['lat'],
    #                     longitude=json.loads(res.object).get('lon') or json.loads(res.object).get('center')['lon']
    #                 )
    #             ]
    #         )
    #     ) for res in results if res.is_found
    # ]
    #
    # session_id = (await ms.CreateSession(
    #     user_id,
    #     features=features
    # )).session_uuid

    density = await dc.CalculateDensity(update.message.location.latitude, update.message.location.longitude)
    res_area = json.loads(density.residential_area or '{}')
    if res_area.get('geometry'):
        res_area.pop('geometry')
    if pr := res_area.get('properties'):
        if 'nodes' in pr.keys():
            res_area['properties'].pop('nodes')

    message += (f'Площадь квартала: {int(round(density.residential_area_size or 0, -1))}м².\n'
                f'Площадь застройки: {int(round(density.buildings_area_size, -1))}м² ({round(density.built_percent, 1)}%).\n'
                f'Общая площадь жилых зданий: {int(round(density.living_buildings_area, 0))}м².\n'
                f'Общая площадь нежилых зданий: {int(round(density.non_living_buildings_area, 0))}м².\n'
                f'Плотность застройки: {int(round(density.buildings_density, 0))}м² на гектар.\n'
                f'Плотность жилой застройки: {int(round(density.living_buildings_density, 0))}м² на гектар.\n'
                f'Ориентировочный максимум жильцов в квартале: {int(round(density.living_buildings_density, 0))} чел.\n'
                f'Ориентировочная плотность расселения: {int(round(density.people_density, 0))} чел. на гектар.\n'
                f'Ориентировочная незастроенная территория на человека: {int(round(density.free_area_per_person, 0))}м² на чел.\n')
    # json_data = json.dumps(
    #     {
    #         'is_residential_found': density.is_residential_found,
    #         'residential_area': res_area,
    #         'residential_area_size': round(density.residential_area_size or 0, 2),
    #         'is_building_found': density.is_building_found,
    #         'buildings': len(json.loads(density.buildings)['features']) if density.buildings else "",
    #         'buildings_area_size': round(density.buildings_area_size, 2),
    #         'built_percent': round(density.built_percent, 2),
    #     }
    # )
    pie = await make_a_pie(density.living_buildings_area, density.non_living_buildings_area)

    await update.message.reply_photo(pie, message)
    # await update.message.reply_photo(pie, message + f'<a href="{settings.MAP_URL}?session_id={session_id}">Посмотреть на карте</a>', parse_mode=telegram.constants.ParseMode.HTML)
