import time

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from redis_session import RedisSession

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int, interval: int, redis_session: RedisSession, key_prefix: str = "ratelimit_"):
        self.limit = limit  # Максимальное количество запросов
        self.interval = interval  # Интервал в секундах
        self.redis_session = redis_session
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

        # Формируем ключ для пользователя в Redis
        redis_key = f"{self.key_prefix}{user_id}"

        # Получаем список временных меток запросов пользователя
        user_requests = await self.redis_session.get_session(redis_key)

        # Если данные отсутствуют или это не список, инициализируем пустым списком
        if not isinstance(user_requests, list):
            user_requests = []

        current_time = time.time()

        # Оставляем только те запросы, которые сделаны в пределах интервала
        user_requests = [timestamp for timestamp in user_requests if current_time - timestamp < self.interval]

        if len(user_requests) >= self.limit:
            # Если количество запросов превышает лимит, отправляем сообщение об ограничении
            if hasattr(event, "message") and event.message:
                await event.message.answer("Вы слишком часто отправляете запросы. Пожалуйста, подождите.")
            elif hasattr(event, "callback_query") and event.callback_query:
                await event.callback_query.answer("Вы слишком часто отправляете запросы. Пожалуйста, подождите.")
            return

        # Добавляем текущий запрос в список и обновляем его в Redis
        user_requests.append(current_time)
        await self.redis_session.set_session(redis_key, user_requests)

        # Передаем управление следующему обработчику
        return await handler(event, data)
