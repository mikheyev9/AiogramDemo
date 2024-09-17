class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url

    async def check_user_exists(self, telegram_id, session):
        """Проверка, существует ли пользователь с данным telegram_id на бэкенде."""
        async with session.get(f"{self.base_url}/auth/check_user/{telegram_id}") as resp:
            if resp.status == 200:
                return await resp.json()  # Ожидаем, что сервер вернет True или False
            return False  # Если запрос завершился с ошибкой, возвращаем False

    async def register(self, telegram_id, password, session):
        print(f"Registering {telegram_id}...{ password, session}")
        async with session.post(f"{self.base_url}/auth/register",
                                json={"telegram_id": str(telegram_id), "password": password}) as resp:
            return await resp.json()

    async def login(self, telegram_id, password, session):
        async with session.post(f"{self.base_url}/auth/login",
                                data={"username": telegram_id, "password": password}) as resp:
            return await resp.json()

    async def get_notes(self, token, session):
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(f"{self.base_url}/notes/notes", headers=headers) as resp:
            return await resp.json()


    async def create_note(self, token, title, content, tags, session):
        headers = {"Authorization": f"Bearer {token}"}
        async with session.post(f"{self.base_url}/notes/notes",
                                json={"title": title, "content": content, "tags": tags},
                                headers=headers) as resp:
            return await resp.json()

    async def search_notes_by_tags(self, token, tags, session):
        headers = {"Authorization": f"Bearer {token}"}
        tags_query = " ".join(tags)
        async with session.get(f"{self.base_url}/notes/notes/search?tags={tags_query}", headers=headers) as resp:
            return await resp.json()

