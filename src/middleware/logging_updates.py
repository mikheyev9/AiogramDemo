from aiogram import BaseMiddleware
from aiogram.types import Update

async def log_incoming_update(logger, update):
    await logger.info(f"Incoming update: {update}")

class LoggingMiddleware(BaseMiddleware):
    def __init__(self, logger):
        self.logger = logger

    async def __call__(self, handler, event: Update, data: dict):
        await log_incoming_update(self.logger, event)
        return await handler(event, data)
