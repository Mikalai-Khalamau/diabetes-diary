import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api import foods, glucose_events, insulin_events, meal_events, recent

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    stream=sys.stdout,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Diabetes Diary API",
    description="API для ведения дневника диабетика",
    version="0.1.0",
)

app.include_router(foods.router)
app.include_router(glucose_events.router)
app.include_router(insulin_events.router)
app.include_router(meal_events.router)
app.include_router(recent.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = Path.cwd() / "frontend"

@app.get("/", include_in_schema=False)
async def serve_frontend():
    if frontend_path.exists():
        return FileResponse(frontend_path / "index.html")
    return {"message": "Frontend not found"}

if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.on_event("startup")
async def startup_event():
    logger.info("Приложение запускается")
    logger.info(f"База данных: {settings.database_url}")
    logger.info(f"Часовой пояс: {settings.app_timezone}")
    logger.info(f"Углеводов в ХЕ: {settings.carbs_per_bread_unit}")
    logger.info("Приложение запущено")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Приложение останавливается")

@app.get("/healthz", tags=["health"])
def health_check():
    return {"status": "ok"}