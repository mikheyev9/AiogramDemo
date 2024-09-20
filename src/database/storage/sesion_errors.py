import functools
import redis.asyncio as aioredis



def handle_redis_errors(fallback_storage, logger):
    """
    Декоратор для обработки ошибок подключения к Redis и fallback на локальное хранилище.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except aioredis.ConnectionError as e:
                await logger.error(f"Ошибка подключения к Redis при вызове {func.__name__}: {str(e)}")
                return await fallback_storage(self, *args, **kwargs)
        return wrapper
    return decorator



class RedisSessionMeta(type):
    def __new__(cls, name, bases, dct):
        for key, value in dct.items():
            if callable(value) and not key.startswith("__"):
                dct[key] = handle_redis_errors(
                    fallback_storage=lambda self, *args, **kwargs: self.local_storage.get_data(chat=args[0])
                )(value)
        return super().__new__(cls, name, bases, dct)