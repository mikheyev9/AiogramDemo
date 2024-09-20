import asyncio
import json

import redis.asyncio as aioredis
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage


class storageSession:
    def __init__(self, redis_host, redis_port, logger):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_url = f"redis://{redis_host}:{redis_port}"
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
        self.logger = logger
        self.use_memory_storage = False
        self.local_storage = MemoryStorage()

    async def get_storage_session(self):
        """
        Проверяет доступность Redis. Если Redis недоступен, возвращает MemoryStorage, иначе RedisStorage.
        """
        try:
            await self.redis.ping()
            await self.logger.info("Redis sucess.")
            return RedisStorage.from_url(self.redis_url)
        except aioredis.ConnectionError as e:
            await self.logger.error(f"Fall Redis: {str(e)}")
            await self.logger.warning("Use MemoryStorage.")
            return MemoryStorage()

    async def get_token(self, user_id):
        if self.use_memory_storage:
            return await self.local_storage.get_data(chat=user_id)
        token = await self.redis.get(f'token:{user_id}')
        return token

    async def set_token(self, user_id, token):
        if self.use_memory_storage:
            await self.local_storage.set_data(chat=user_id, data={"token": token})
        else:
            await self.redis.set(f'token:{user_id}', token)

    async def get_session(self, user_id):
        if self.use_memory_storage:
            return await self.local_storage.get_data(chat=user_id)
        session = await self.redis.get(f'session:{user_id}')
        if session:
            return json.loads(session)
        else:
            session = {}
            await self.redis.set(f'session:{user_id}', json.dumps(session))
        return session

    async def set_session(self, user_id, session_data):
        if self.use_memory_storage:
            await self.local_storage.set_data(chat=user_id, data=session_data)
        else:
            await self.redis.set(f'session:{user_id}', json.dumps(session_data))

    async def get_last_activity(self, user_id):
        if self.use_memory_storage:
            data = await self.local_storage.get_data(chat=user_id)
            return data.get('last_activity')
        last_activity = await self.redis.get(f'last_activity:{user_id}')
        return float(last_activity) if last_activity else None

    async def update_last_activity(self, user_id):
        if self.use_memory_storage:
            await self.local_storage.set_data(chat=user_id, data={"last_activity": asyncio.get_event_loop().time()})
        else:
            await self.redis.set(f'last_activity:{user_id}', asyncio.get_event_loop().time())

    async def clear_token(self, user_id):
        if self.use_memory_storage:
            await self.local_storage.clear_data(chat=user_id)
        else:
            await self.redis.delete(f'token:{user_id}')

