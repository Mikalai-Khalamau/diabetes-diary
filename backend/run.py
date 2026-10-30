import uvicorn
import json
import logging
from datetime import datetime, timezone
from app.config import settings


class UvicornJSONFormatter:
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service.name": "diabetes-diary",
            "logger": record.name,
        }
        return json.dumps(log_record, ensure_ascii=False)


class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        health_endpoints = ['/healthz', '/readyz']
        for endpoint in health_endpoints:
            if endpoint in message:
                return False
        return True


log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": UvicornJSONFormatter,
        },
    },
    "filters": {
        "health_check_filter": {
            "()": HealthCheckFilter,
        },
    },
    "handlers": {
        "default": {
            "formatter": "json",
            "filters": ["health_check_filter"],
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default"],
            "level": settings.log_level.upper(),
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": settings.log_level.upper(),
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["default"],
            "filters": ["health_check_filter"],
            "level": settings.log_level.upper(),
            "propagate": False,
        },
    },
}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        log_level=settings.log_level.lower(),
        log_config=log_config,
    )