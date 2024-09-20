import time

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int, interval: int, session, key_prefix: str = "ratelimit_"):
        self.limit = limit  # Максимальное количество запросов
        self.interval = interval  # Интервал в секундах
        self.redis_session = session
        self.key_prefix = key_prefix  # Префикс для ключей в Redis
        super().__init__()

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None
        if hasattr(event, "message") and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif hasattr(event, "callback_query") and event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id
        else:
            return
        redis_key = f"{self.key_prefix}{user_id}"

        user_requests = await self.redis_session.get_session(redis_key)
        if not isinstance(user_requests, list):
            user_requests = []

        current_time = time.time()

        user_requests = [timestamp for timestamp in user_requests if current_time - timestamp < self.interval]

        if len(user_requests) >= self.limit:
            if hasattr(event, "message") and event.message:
                await event.message.answer("Вы слишком часто отправляете запросы. Пожалуйста, подождите.")
            elif hasattr(event, "callback_query") and event.callback_query:
                await event.callback_query.answer("Вы слишком часто отправляете запросы. Пожалуйста, подождите.")
            return

        user_requests.append(current_time)
        await self.redis_session.set_session(redis_key, user_requests)

        return await handler(event, data)
