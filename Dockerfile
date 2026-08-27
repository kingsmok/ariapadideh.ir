# syntax=docker/dockerfile:1
# ============================================================================
# Flask Pro — Production image (Gunicorn + Celery از همین ایمیج اجرا می‌شوند)
# ============================================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# libmagic1 برای python-magic (اعتبارسنجی MIME آپلود مدیا) لازم است؛
# curl برای healthcheck وب. build-essential فقط در مرحله builder.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# لایه وابستگی‌ها — کش‌فرندلی: تا requirements.txt دست نخورده، pip اجرا نمی‌شود
COPY requirements.txt ./
RUN pip install -r requirements.txt

# کد برنامه
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY docker/entrypoint.sh ./docker/
COPY run.py worker.py gunicorn.conf.py ./
RUN chmod +x /app/docker/entrypoint.sh \
    && mkdir -p /app/instance /app/logs /app/app/static/uploads \
    && useradd --create-home --uid 10001 flaskpro \
    && chown -R flaskpro:flaskpro /app
USER flaskpro

# سلامت‌سنی ساده؛ compose از آن به‌جای busybox wget استفاده می‌کند
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

EXPOSE 8000

# پیش‌فرض: وب. در compose، worker/beat با command متفاوت همین ایمیج را اجرا می‌کنند.
# تنظیمات gunicorn از gunicorn.conf.py (کنار CMD) بارگذاری می‌شود — تعداد ورکر
# از WEB_CONCURRENCY و bind از GUNICORN_BIND قابل override است.
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "app:create_app()"]
