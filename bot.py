import asyncio

from aiogram import Bot, Dispatcher

from src.middleware.session_middleware import UnifiedSessionMiddleware
from src.middleware.rate_limit_middleware import RateLimitMiddleware
from src.handlers.start import start_router
from src.handlers.register import login_router
from src.handlers.notes import notes_router
from src.database import storageSession
from config import Config
from logs import AsyncLoggerSingleton
from src.middleware import LoggingMiddleware


async def main():
    logger_singleton = AsyncLoggerSingleton(log_file_path=Config.LOG_PATH)
    logger = await logger_singleton.get_logger()


    session_manager = storageSession(redis_host=Config.REDIS_HOST,
                                     redis_port=Config.REDIS_PORT,
                                     logger=logger)

    session = await session_manager.get_storage_session()

    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=session)

    dp.update.middleware(LoggingMiddleware(logger))
    dp.update.middleware(RateLimitMiddleware(limit=50, interval=60,
                                             session=session_manager))
    dp.update.middleware(UnifiedSessionMiddleware(session=session_manager,
                                                  base_url=Config.BASE_URL))


    dp.include_router(start_router)
    dp.include_router(login_router)
    dp.include_router(notes_router)

    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
