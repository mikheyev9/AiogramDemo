import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.callback_data import CallbackData

from src.middleware.session_middleware import UnifiedSessionMiddleware
from src.middleware.rate_limit_middleware import RateLimitMiddleware
from src.handlers.start import start_router
from src.handlers.register import login_router
from src.handlers.notes import notes_router
from redis_session import RedisSession
from config import Config

class NoteCallbackData(CallbackData, prefix="action"):
    action_type: str

async def main():
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    redis_session = RedisSession(redis_host=Config.REDIS_HOST, redis_port=Config.REDIS_PORT)
    dp.update.middleware(RateLimitMiddleware(limit=50, interval=60, redis_session=redis_session))
    dp.update.middleware(UnifiedSessionMiddleware(redis_session=redis_session, base_url=Config.BASE_URL))

    dp.include_router(start_router)
    dp.include_router(login_router)
    dp.include_router(notes_router)

    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
