from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from redis_session import RedisSession
from ..services.api_service import ApiClient
from .start import get_main_menu, get_login_button

notes_router = Router()

async def __need_login(notes, redis_session, callback):
    if isinstance(notes, dict) and notes.get('detail') == 'Could not validate credentials':
        await redis_session.clear_token(callback.from_user.id)
        await callback.message.answer(
            "Ваш токен недействителен. Пожалуйста, авторизуйтесь снова.",
            reply_markup=get_login_button()
        )
        return True

async def __need_login_and_fetch_notes(fetch_func, token, redis_session, user_id, message_or_callback):
    notes = await fetch_func(token)

    # Проверка на то, что токен недействителен
    if isinstance(notes, dict) and notes.get('detail') == 'Could not validate credentials':
        await redis_session.clear_token(user_id)
        await message_or_callback.answer(
            "Ваш токен недействителен. Пожалуйста, авторизуйтесь снова.",
            reply_markup=get_login_button()
        )
        return None
    return notes

# Получение списка заметок с форматированием
@notes_router.callback_query(lambda c: c.data == "get_notes")
async def get_notes(callback: types.CallbackQuery, api_client: ApiClient, redis_session: RedisSession, aiohttp_session):
    token = await redis_session.get_token(callback.from_user.id)

    if token:

        notes = await __need_login_and_fetch_notes(
            lambda t: api_client.get_notes(t, aiohttp_session),
            token,
            redis_session,
            callback.from_user.id,
            callback.message
        )

        if notes is None:  # Токен недействителен
            return
        if isinstance(notes, list) and notes:
            formatted_notes = "\n\n".join([
                f"Заметка #{note['id']}\nЗаголовок: {note['title']}\n"
                f"Содержание: {note['content']}\n"
                f"Теги: {', '.join(tag['name'] for tag in note['tags']) if note['tags'] else 'нет'}\n"
                f"Создано: {note['created_at']}\nОбновлено: {note['updated_at']}"
                for note in notes
            ])
        else:
            formatted_notes = "У вас пока нет заметок."

        await callback.message.answer(f"Ваши заметки:\n{formatted_notes}", reply_markup=get_main_menu())

    else:
        await callback.message.answer(
            "Пожалуйста, авторизуйтесь сначала.",
            reply_markup=get_login_button()
        )


# Создание новой заметки
@notes_router.callback_query(lambda c: c.data == "create_note")
async def create_note_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите заголовок заметки:")
    await state.set_state("awaiting_note_title")


@notes_router.message(StateFilter("awaiting_note_title"))
async def process_note_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Теперь введите содержание заметки:")
    await state.set_state("awaiting_note_content")


@notes_router.message(StateFilter("awaiting_note_content"))
async def process_note_content(message: types.Message,
                               state: FSMContext,
                               api_client: ApiClient,
                               redis_session: RedisSession,
                               aiohttp_session):
    data = await state.get_data()
    title = data.get("title")
    content = message.text
    token = await redis_session.get_token(message.from_user.id)

    await message.answer(
        "Теперь введите теги через пробел (например: работа учеба личное). Если не хотите добавлять теги, просто отправьте пустое сообщение.")
    await state.update_data(content=content)
    await state.set_state("awaiting_note_tags")


# Обработка тегов и создание заметки
@notes_router.message(StateFilter("awaiting_note_tags"))
async def process_note_tags(message: types.Message,
                            state: FSMContext,
                            api_client: ApiClient,
                            redis_session: RedisSession,
                            aiohttp_session):
    data = await state.get_data()
    title = data.get("title")
    content = data.get("content")
    token = await redis_session.get_token(message.from_user.id)

    # Получаем теги, если есть
    tags = message.text.split() if message.text else []

    if token:
        response = await api_client.create_note(token, title, content, tags, aiohttp_session)
        print(response)
        # Форматируем ответ для красивого вывода
        created_note = (
            f"Заметка создана!\n\n"
            f"Заголовок: {response['title']}\n"
            f"Содержание: {response['content']}\n"
            f"Теги: {', '.join(tag['name'] for tag in response['tags']) if response['tags'] else 'нет'}\n"
            f"Создано: {response['created_at']}\nОбновлено: {response['updated_at']}"
        )

        await message.answer(created_note, reply_markup=get_main_menu())
    else:
        await message.answer("Не удалось создать заметку. Попробуйте снова.", reply_markup=get_main_menu())

    await state.clear()


# Запрос ввода тегов для поиска заметок
@notes_router.callback_query(lambda c: c.data == "search_notes_by_tag")
async def search_notes_by_tag_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите теги для поиска (разделяйте пробелами):")
    await state.set_state("awaiting_tag_search")


# Обработка тегов и поиск заметок
@notes_router.message(StateFilter("awaiting_tag_search"))
async def process_tag_search(message: types.Message,
                             state: FSMContext,
                             api_client: ApiClient,
                             redis_session: RedisSession,
                             aiohttp_session):
    tags = message.text.split()  # Получаем теги от пользователя (через пробел)
    token = await redis_session.get_token(message.from_user.id)

    if token:
        # Используем новый метод для поиска по нескольким тегам
        notes = await __need_login_and_fetch_notes(
            lambda t: api_client.search_notes_by_tags(t, tags, aiohttp_session),
            token,
            redis_session,
            message.from_user.id,
            message
        )
        if notes is None:  # Токен недействителен
            return

            # Форматируем результат поиска
        if isinstance(notes, list) and notes:
            formatted_notes = "\n\n".join([
                f"Заметка #{note['id']}\nЗаголовок: {note['title']}\n"
                f"Содержание: {note['content']}\n"
                f"Теги: {', '.join(tag['name'] for tag in note['tags']) if note['tags'] else 'нет'}\n"
                f"Создано: {note['created_at']}\nОбновлено: {note['updated_at']}"
                for note in notes
            ])
        else:
            formatted_notes = "Заметок с такими тегами не найдено."

        await message.answer(f"Результаты поиска:\n{formatted_notes}", reply_markup=get_main_menu())

    else:
        await message.answer(
            "Пожалуйста, авторизуйтесь сначала.",
            reply_markup=get_login_button()
        )

    await state.clear()
