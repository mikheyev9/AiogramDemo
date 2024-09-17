import redis.asyncio as aioredis
import asyncio
import json


class RedisSession:
    def __init__(self, redis_host, redis_port=6379):
        self.redis = aioredis.from_url(f"redis://{redis_host}:{redis_port}",
                                       decode_responses=True)

    async def get_token(self, user_id):
        token = await self.redis.get(f'token:{user_id}')
        return token

    async def set_token(self, user_id, token):
        await self.redis.set(f'token:{user_id}', token)

    async def get_session(self, user_id):
        session = await self.redis.get(f'session:{user_id}')
        if session:
            return json.loads(session)
        else:
            session = {}
            await self.redis.set(f'session:{user_id}', json.dumps(session))
        print(session)
        return session

    async def set_session(self, user_id, session_data):
        # Сериализация данных сессии в строку перед сохранением
        await self.redis.set(f'session:{user_id}', json.dumps(session_data))

    async def get_last_activity(self, user_id):
        last_activity = await self.redis.get(f'last_activity:{user_id}')
        return float(last_activity) if last_activity else None

    async def update_last_activity(self, user_id):
        await self.redis.set(f'last_activity:{user_id}', asyncio.get_event_loop().time())

    async def clear_token(self, user_id):
        await self.redis.delete(f'token:{user_id}')
