FROM python:3.12-slim

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
COPY backend/src ./src
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY backend/app ./app
COPY backend/bot ./bot

EXPOSE 8000

CMD ["sh", "-c", "uv run --no-dev alembic upgrade head && uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port 8000"]