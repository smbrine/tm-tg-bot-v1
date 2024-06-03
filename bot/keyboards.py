from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


async def get_start_keyboard(
    is_phone_confirmed: bool = False,
    is_admin: bool = False,
):
    buttons = [
        [
            KeyboardButton(
                text="Отправить мое местоположение",
                request_location=True,
            ),
        ],
        [
            KeyboardButton(
                text="Сообщить об ошибке",
            ),
        ],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        is_persistent=True,
    )


async def get_cafe_card_ext_buttons(
    latitude: float, longitude: float
):
    buttons = [
        [
            InlineKeyboardButton(
                text="Где это?",
                callback_data=f"inline:send:loc:{latitude}:{longitude}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


async def get_cafe_card_buttons(
    current: int,
    total: int,
    lat: float,
    lon: float,
):
    buttons = [
        [
            InlineKeyboardButton(
                text="<-",
                callback_data="switch:backwards",
            ),
            InlineKeyboardButton(
                text=f"{current}/{total}",
                callback_data="switch:pass",
            ),
            InlineKeyboardButton(
                text="->",
                callback_data="switch:forward",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Где это?",
                callback_data=f"send:loc:{lat}:{lon}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


async def get_settings_keyboard(
    is_phone_confirmed: bool,
):
    buttons = [
        [
            KeyboardButton(
                text="Искать рядом",
                request_location=True,
            ),
        ],
        [
            KeyboardButton(
                text="Профиль",
            ),
        ]
        + (
            [
                KeyboardButton(
                    text="Подтвердить номер телефона",
                    request_contact=True,
                ),
            ]
            if not is_phone_confirmed
            else []
        ),
        [
            KeyboardButton(
                text="Предложить кофейню",
            ),
            KeyboardButton(
                text="Сообщить об ошибке",
            ),
        ],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        is_persistent=True,
    )
