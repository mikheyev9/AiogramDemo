import aiohttp
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from ..services.api_service import ApiClient

class UnifiedSessionMiddleware(BaseMiddleware):
    def __init__(self, session, base_url: str, session_timeout: int = 120):
        self.redis_session = session
        self.base_url = base_url
        self.session_timeout = session_timeout
        self.aiohttp_sessions = {}
        super().__init__()

    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Проверяем, есть ли у события from_user
        user_id = None
        if hasattr(event, "message") and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif hasattr(event, "callback_query") and event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id
        else:
            print('Не удается получить информацию о пользователе')
            return


        if not user_id:
            if hasattr(event, "message"):
                await event.message.answer("Не удается получить информацию о пользователе.")
            elif hasattr(event, "callback_query"):
                await event.callback_query.answer("Не удается получить информацию о пользователе.")
            return

        # Получаем Redis сессию
        session_data = await self.redis_session.get_session(user_id)
        data['session'] = session_data

        # Проверяем токен
        token = await self.redis_session.get_token(user_id)


        # Создаем или восстанавливаем `aiohttp` сессию
        if user_id not in self.aiohttp_sessions or self.aiohttp_sessions[user_id].closed:
            self.aiohttp_sessions[user_id] = aiohttp.ClientSession()

        aiohttp_session = self.aiohttp_sessions[user_id]
        api_client = ApiClient(base_url=self.base_url)

        # Передаем необходимые объекты в data
        data['aiohttp_session'] = aiohttp_session
        data['api_client'] = api_client
        data['redis_session'] = self.redis_session

        # Передаем управление следующему обработчику
        return await handler(event, data)


