"""FastAPI entry point for PyPlanner backend."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.database import create_db_and_tables
from app.backend.routers import categories, recipes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create DB tables on startup."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="PyPlanner API",
    description="Backend para la aplicación de gestión de recetas y menús semanales.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(recipes.router)
app.include_router(categories.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Verificar que el servidor está corriendo."""
    return {"status": "ok"}
