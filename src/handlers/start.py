from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from redis_session import RedisSession
from ..services.api_service import ApiClient

start_router = Router()  # Создаем один маршрутизатор


def get_main_menu() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Получить список заметок", callback_data="get_notes")
    builder.button(text="Создать новую заметку", callback_data="create_note")
    builder.button(text="Поиск заметок по тегам", callback_data="search_notes_by_tag")
    builder.adjust(1)
    return builder.as_markup()

def get_start_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="Регистрация", callback_data="start")
    return builder.as_markup()

def get_login_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="Войти", callback_data="login")
    return builder.as_markup()


@start_router.message(Command(commands=["start"]))
async def handle_start(message: types.Message, api_client: ApiClient, redis_session: RedisSession, aiohttp_session):
    token = await redis_session.get_token(message.from_user.id)
    user_exists = await api_client.check_user_exists(message.from_user.id, aiohttp_session)
    if token and user_exists:
        await message.answer("Вы уже авторизованы!", reply_markup=get_main_menu())
    else:
        user_exists = await api_client.check_user_exists(message.from_user.id, aiohttp_session)
        if user_exists:
            await message.answer("Пожалуйста, войдите в систему.", reply_markup=get_login_button())
        else:
            await message.answer("Нажмите 'Регистрация' для создания аккаунта.",
                                 reply_markup=get_start_button())