from contextlib import asynccontextmanager

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update

from app import settings
from bot.main import bot, dp
from db import models
from db.main import get_db, sessionmanager
from utils import RedisWrapper


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    sessionmanager.init(settings.POSTGRES_URL)

    if bot:
        response = await bot.get_webhook_info()
        if settings.DEBUG:
            print(response)
        webhook_url = f"{settings.PUBLIC_ADDR}/webhook?token={settings.TG_BOT_KEY}"
        if settings.DEBUG:
            print(webhook_url)
        while response.url != webhook_url:
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=Update.ALL_TYPES,
            )
            response = (
                await bot.get_webhook_info()
            )
            if settings.DEBUG:
                print(response)
        await dp.initialize()
    yield
    if (
        sessionmanager._engine is not None
    ):  # pylint: disable=W0212  #
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)
redis = RedisWrapper(settings.REDIS_URL)


@app.post("/webhook")
async def webhook(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    if token != settings.TG_BOT_KEY:
        raise HTTPException(
            status_code=401, detail="Unauthorized"
        )
    data = await request.json()
    upd = Update.de_json(data, bot)

    upd_type = (data.keys() - {"update_id"}).pop()
    user = upd.effective_user
    if not (
        user_in_db := await models.User.get_by_telegram_id(
            db, user.id
        )
    ):
        user_in_db = await models.User.create(
            db,
            telegram_id=user.id,
            is_bot=user.is_bot,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            language_code=user.language_code,
            is_premium=user.is_premium,
        )

    await dp.process_update(upd)
    await user_in_db.add_update(
        db,
        update_id=upd.update_id,
        update_type=upd_type,
        update_data=upd.to_dict(),
    )
    return JSONResponse(
        content={"message": "ok"}, status_code=200
    )


@app.get("/healthz")
async def healthz():
    return JSONResponse(
        status_code=200, content={"health": "ok"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BIND_HOST,
        port=settings.BIND_PORT,
        reload=settings.DEBUG,
        log_level=0,
        use_colors=True,
    )
