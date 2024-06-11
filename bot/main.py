import logging


from telegram import (
    Bot,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)
from app import settings
from utils import DensityCalculator, DistanceCalculator, MapSessions

bot = Bot(token=settings.TG_BOT_KEY)
dp = ApplicationBuilder().bot(bot).build()
pb = DistanceCalculator(host=settings.DISTANCE_CALCULATOR_GRPC)
ms = MapSessions(host=settings.MAP_SESSIONS_GRPC)
dc = DensityCalculator(host=settings.DENSITY_CALCULATOR_GRPC)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(
    logging.DEBUG
    if settings.DEBUG
    else logging.WARNING
)

logger = logging.getLogger(__name__)


def main() -> None:
    from bot import handlers

    dp.add_handler(
        CommandHandler(
            "start", handlers.command_start
        )
    )
    dp.add_handler(
        MessageHandler(
            filters.LOCATION,
            handlers.message_location,
        )
    )


main()

if __name__ == "__main__":
    dp.run_polling(
        allowed_updates=Update.ALL_TYPES
    )
