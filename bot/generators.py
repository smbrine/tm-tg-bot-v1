import json


async def my_round(distance):
    if distance < 1000:
        return f'{int(round(distance, 0))}м'
    return f'{round(distance/1000, 2)}км'

async def generate_distance_card(
    is_found: bool,
    name: str,
    distance: int | float,
    obj: dict,
    search_distance: int | float,
):
    if not is_found:
        msg = f"Не нашел {name} в радиусе {await my_round(search_distance)}."
    else:
        msg = f"Нашел {name} в {await my_round(distance)} от указанного места."
        # msg += f'<pre language="json">{json.dumps(obj, ensure_ascii=False)}</pre>'
    return msg
