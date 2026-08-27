"""
Health Service — بررسی سلامت وابستگی‌ها برای LB / اورکستراتور / مانیتورینگ

سیاست وضعیت (متناسب با طراحی graceful-degradation خودِ برنامه):

- دیتابیس ناسالم        → status=down    + HTTP 503  (ترافیک نباید روت شود)
- Redis/بروکر ناسالم    → status=degraded + HTTP 200 (سرویس با fallback ادامه می‌دهد؛
  کش/سشن‌سرور/Celery اختیاری‌اند ولی باید در متریک‌ها دیده شوند)
- همه سالم              → status=healthy  + HTTP 200

هیچ‌گاه اطلاعات حساس (connection string، نسخه دقیق دیتابیس، stacktrace) در
پاسخ بیرونی قرار نمی‌گیرد؛ جزئیات فقط در لاگ ثبت می‌شود.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Tuple

from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

#: آستانهٔ اعلام latency غیرعادی دیتابیس (میلی‌ثانیه) — صرفاً برای هشدار لاگ
DB_LATENCY_WARN_MS = 250


class HealthService:
    """Probe runner for infra dependencies."""

    @staticmethod
    def check_database() -> Dict[str, Any]:
        """کوئری سبک ``SELECT 1`` روی استخر اتصال‌ها.

        Returns:
            ``{'ok': bool, 'latency_ms': float, 'error': str | None}``
        """
        from app.extensions import db

        started = time.perf_counter()
        try:
            db.session.execute(text('SELECT 1'))
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            if latency_ms > DB_LATENCY_WARN_MS:
                logger.warning('DB health probe slow: %s ms', latency_ms)
            return {'ok': True, 'latency_ms': latency_ms, 'error': None}
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error('DB health probe failed: %s', exc, exc_info=True)
            return {'ok': False, 'latency_ms': None, 'error': type(exc).__name__}
        except Exception as exc:  # noqa: BLE001 — هر خطای زیرساختی = ناسالم
            logger.error('DB health probe crashed: %s', exc, exc_info=True)
            return {'ok': False, 'latency_ms': None, 'error': type(exc).__name__}

    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """پینگ کلاینت کشِ جهانی (اگر در این پروسه ساخته شده باشد).

        نبودِ Redis یعنی برنامه از قبل روی fallback است؛ این حالت degraded
        شمرده می‌شود نه down.
        """
        from app.extensions import redis_client

        if redis_client is None:
            return {'ok': False, 'latency_ms': None, 'error': 'not_initialized', 'optional': True}
        started = time.perf_counter()
        try:
            redis_client.ping()
            return {'ok': True,
                    'latency_ms': round((time.perf_counter() - started) * 1000, 2),
                    'error': None, 'optional': True}
        except Exception as exc:  # noqa: BLE001
            logger.warning('Redis health probe failed: %s', exc)
            return {'ok': False, 'latency_ms': None, 'error': type(exc).__name__, 'optional': True}

    @staticmethod
    def check_task_queue() -> Dict[str, Any]:
        """وضعیت صف تسک‌ها.

        دو حالت قابل‌تفکیک مهم است:
        - ``CELERY_ENABLED=false`` → queue «disabled» (فیل‌سیف نیست؛ inline fallback فعال است)
        - روشن ولی broker بی‌پاسخ → ``{'ok': False}`` که degraded می‌شود
        """
        try:
            if not current_app.config.get('CELERY_ENABLED', False):
                return {'ok': True, 'state': 'disabled', 'error': None}
            from app.tasks.celery_app import celery
            inspect = celery.inspect(timeout=1.0)
            replies = inspect.ping() if inspect else None
            workers = len(replies) if replies else 0
            return {
                'ok': workers > 0,
                'state': 'up' if workers > 0 else 'no_workers',
                'workers': workers,
                'error': None if workers else 'no_workers_responding',
            }
        except Exception as exc:  # noqa: BLE001 — healthcheck هرگز نباید 500 بدهد
            logger.warning('Task-queue probe failed: %s', exc)
            return {'ok': False, 'state': 'unreachable', 'error': type(exc).__name__}

    @classmethod
    def snapshot(cls) -> Tuple[Dict[str, Any], int]:
        """اجرای همهٔ پروب‌ها و ساخت بدنهٔ پاسخ + کد HTTP مناسب.

        Returns:
            (body, status_code) — body شامل وضعیت کلی، چک‌ها و timestamp است.
        """
        checks: Dict[str, Any] = {
            'database': cls.check_database(),
            'redis': cls.check_redis(),
            'tasks': cls.check_task_queue(),
        }

        if not checks['database']['ok']:
            overall, status = 'down', 503
        elif any(not c['ok'] for c in (checks['redis'], checks['tasks'])):
            overall, status = 'degraded', 200
        else:
            overall, status = 'healthy', 200

        body = {
            'status': overall,
            'checks': checks,
            'timestamp': round(time.time(), 3),
        }
        return body, status
