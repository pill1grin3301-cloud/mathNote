import os

os.environ.setdefault(
    "DATABASE_URL",
    os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://mathnote:test@localhost:5432/mathnote_test",
    ),
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-enough-entropy")
os.environ["TELEGRAM_TOKEN"] = ""
