import time
import requests
import logging
from datetime import datetime, timezone

from app.config import settings
from app.prober_metrics import PROBER_CHECKS_TOTAL, PROBER_CHECK_DURATION_SECONDS
from prometheus_client import start_http_server

logger = logging.getLogger(__name__)

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "test12345"
BASE_URL = f"http://diabetes-app"


def run_prober():
    logger.info("Пробер запущен")
    token = None

    while True:
        try:
            check_name = "healthz"
            start_time = time.time()
            try:
                response = requests.get(f"{BASE_URL}/healthz", timeout=5)
                if response.status_code == 200:
                    PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="success").inc()
                else:
                    PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                    logger.warning(f"Health check failed: status={response.status_code}")
            except Exception as e:
                PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                logger.error(f"Health check error: {e}")

            duration = time.time() - start_time
            PROBER_CHECK_DURATION_SECONDS.labels(check_name=check_name).observe(duration)

            check_name = "login"
            start_time = time.time()
            try:
                if token is None:
                    response = requests.post(
                        f"{BASE_URL}/api/auth/login",
                        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
                        timeout=10
                    )
                    if response.status_code == 200:
                        token = response.json()["access_token"]
                        PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="success").inc()
                    else:
                        PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                        logger.warning(f"Login failed: status={response.status_code}")
                else:
                    PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="success").inc()
            except Exception as e:
                PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                logger.error(f"Login error: {e}")

            duration = time.time() - start_time
            PROBER_CHECK_DURATION_SECONDS.labels(check_name=check_name).observe(duration)

            check_name = "recent_stats"
            start_time = time.time()
            try:
                if token:
                    response = requests.get(
                        f"{BASE_URL}/api/stats/recent",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10
                    )
                    if response.status_code == 200:
                        PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="success").inc()
                    elif response.status_code == 401:
                        token = None
                        PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                        logger.warning("Token expired, will re-login next cycle")
                    else:
                        PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                        logger.warning(f"Recent stats failed: status={response.status_code}")
                else:
                    PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                    logger.warning("No token available, skipping recent stats check")
            except Exception as e:
                PROBER_CHECKS_TOTAL.labels(check_name=check_name, result="failure").inc()
                logger.error(f"Recent stats error: {e}")

            duration = time.time() - start_time
            PROBER_CHECK_DURATION_SECONDS.labels(check_name=check_name).observe(duration)

            time.sleep(30)

        except KeyboardInterrupt:
            logger.info("Пробер остановлен")
            break
        except Exception as e:
            logger.error(f"Unexpected error in prober loop: {e}")
            time.sleep(30)


if __name__ == "__main__":
    start_http_server(8001)
    logger.info("Metrics server started on port 8001")
    run_prober()