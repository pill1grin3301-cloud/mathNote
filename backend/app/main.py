from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.notebooks import router as notebooks_router
from app.config import settings

app = FastAPI(
    title="mathNote API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[*settings.cors_origins],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(auth_router)
app.include_router(notebooks_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
