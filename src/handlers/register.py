from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from redis_session import RedisSession
from ..services.api_service import ApiClient
from ..handlers.start import get_main_menu, get_login_button

login_router = Router()

def get_send_button():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отправить", callback_data="send_password")
    return builder.as_markup()

def get_login_send_button():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отправить", callback_data="send_login_password")
    return builder.as_markup()

@login_router.callback_query(lambda c: c.data == "start")
async def start_registration(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Пожалуйста, введите ваш пароль для регистрации.",
        reply_markup=get_send_button()
    )
    await state.set_state("awaiting_password")

# Обработка нажатия кнопки "Отправить" для регистрации
@login_router.callback_query(lambda c: c.data == "send_password")
async def prompt_for_password(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пожалуйста, введите ваш пароль.")
    await state.set_state("awaiting_password")

# Обработка ввода пароля для регистрации
@login_router.message(StateFilter("awaiting_password"))
async def process_password(message: types.Message, state: FSMContext, api_client: ApiClient, aiohttp_session):
    password = message.text
    response = await api_client.register(message.from_user.id, password, aiohttp_session)
    print(password, response, 'response')

    if "telegram_id" in response:
        await message.answer(
            "Регистрация прошла успешно! Пожалуйста, войдите в систему.",
            reply_markup=get_login_button()
        )
    else:
        await message.answer("Произошла ошибка при регистрации. Попробуйте снова.")

    await state.clear()

# Обработка кнопки "Войти" для входа
@login_router.callback_query(lambda c: c.data == "login")
async def login_user(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Введите пароль для входа:",
        reply_markup=get_login_send_button()
    )
    await state.set_state("awaiting_login_password")

# Обработка нажатия кнопки "Отправить" для входа
@login_router.callback_query(lambda c: c.data == "send_login_password")
async def prompt_for_login_password(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пожалуйста, введите ваш пароль.")
    # Переходим к состоянию ожидания ввода пароля
    await state.set_state("awaiting_login_password")

# Обработка ввода пароля для входа
@login_router.message(StateFilter("awaiting_login_password"))
async def process_login(message: types.Message, state: FSMContext, api_client: ApiClient, redis_session: RedisSession, aiohttp_session):
    password = message.text
    try:
        response = await api_client.login(message.from_user.id, password, aiohttp_session)
    except Exception:
        await message.answer("Произошла ошибка при входе. Попробуйте снова.")
        await state.clear()
        return

    if "access_token" in response:
        await redis_session.set_token(message.from_user.id, response["access_token"])
        await message.answer("Вы успешно вошли!", reply_markup=get_main_menu())
    else:
        await message.answer("Неверный пароль. Попробуйте снова.")

    await state.clear()

