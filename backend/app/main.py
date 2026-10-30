import logging
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api import auth, foods, glucose_events, insulin_events, meal_events, recent
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import create_engine, text

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service.name": "diabetes-diary",
            "logger": record.name,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.upper()))
logger.addHandler(handler)
logger.propagate = False

app = FastAPI(
    title="Diabetes Diary API",
    description="API для ведения дневника диабетика",
    version="0.2.0",
)

app.include_router(auth.router)
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

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

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


@app.get("/readyz", tags=["health"])
def readiness_check():
    try:
        engine = create_engine(
            settings.database_url,
            pool_size=1,
            max_overflow=0,
            pool_timeout=2,
            pool_pre_ping=True,
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        engine.dispose()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "error": str(e)}
        )