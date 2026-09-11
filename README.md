# mathNote

Заметки с формулами: лист как тетрадка, внутри — заголовки, текст, MathLive и рисовалка. Можно работать локально или с аккаунтом: тогда листы синхронизируются с сервером.

Сайт: [mathnote.ru](https://mathnote.ru)

## Что умеет    

- Формулы с шорткатами: дроби, степени, пределы, корни, интегралы, суммы, системы
- Несколько листов, разделы, перетаскивание в боковой панели (`+` слева)
- Автосейв: локально и на сервер (с паузой 7 секунд)
- Светлая / тёмная тема, экспорт и импорт JSON
- Регистрация и вход (JWT). Без входа остаётся локальный черновик

В интерфейсе список клавиш — блок **«Клавиши»** под листом.

## Стек

| Часть | Технологии |
|---|---|
| Фронт | один `index.html`, MathLive |
| API | FastAPI, SQLAlchemy, Alembic |
| База | PostgreSQL 17 |
| Запуск | Docker Compose, nginx для статики |

Лимиты на аккаунт: 30 разделов, 100 листов.

## Локальный запуск

Нужны Docker и файл `backend/.env` (образец — `backend/.env.example`).

```bash
cp backend/.env.example backend/.env
# пропиши POSTGRES_* , DATABASE_URL и SECRET_KEY
docker compose up --build
```

- фронт: http://127.0.0.1:8767
- API: http://127.0.0.1:8042  
- swagger: http://127.0.0.1:8042/docs

Фронт без Docker:

```bash
python3 -m http.server 8767 --bind 127.0.0.1
```

API без Docker (из `backend/`, после поднятой Postgres и миграций):

```bash
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8042
```

## Тесты

```bash
cd backend
uv run pytest
```

Интеграционные тесты к Postgres нужны с `TEST_DATABASE_URL`. В CI это задаёт `.github/workflows/ci.yml`.

## API кратко

JWT на всех ручках, кроме регистрации и входа.

| | |
|---|---|
| `POST /api/auth/register` | ник + пароль, сразу «Лист 1» |
| `POST /api/auth/login` | JWT |
| `GET/POST /api/sections` | разделы |
| `PATCH/DELETE /api/sections/{id}` | имя, порядок, удаление |
| `GET/POST /api/notebooks` | список и новый лист |
| `GET/PUT /api/notebooks/{id}` | документ, optimistic lock (`baseVersion`) |
| `PATCH /api/notebooks/{id}` | название, раздел, порядок — без bump версии |
| `DELETE /api/notebooks/{id}` | последний лист удалить нельзя (409) |

Чужой id выглядит как **404**, не 403.
