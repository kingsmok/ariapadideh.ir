#!/bin/sh
# ============================================================================
# Flask Pro container entrypoint
#  - منتظر آماده‌شدن PostgreSQL/Redis می‌ماند (بدون آن compose startup race دارد)
#  - دقیقاً در پروسه وب، مهاجرت‌ها را اعمال می‌کند (ورکر/beat مهاجرت نمی‌زنند)
#  - سپس CMD اصلی را exec می‌کند
# ============================================================================
set -e

ROLE="${CONTAINER_ROLE:-web}"

if [ "$ROLE" = "web" ] && [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] waiting for database..."
    # تلاش حداکثر ~۶۰ ثانیه؛ بعد از آن اگر هنوز آماده نبود با خطا خارج شو
    i=0
    until python -c "
import os, sys
from sqlalchemy import create_engine, text
uri = os.environ.get('DATABASE_URL')
if not uri or uri.startswith('sqlite'):
    sys.exit(0)  # sqlite محلی نیازی به انتظار ندارد
try:
    create_engine(uri, pool_pre_ping=True, connect_args={'connect_timeout': 3}).connect().execute(text('SELECT 1'))
except Exception:
    sys.exit(1)
"; do
        i=$((i+1))
        if [ "$i" -ge 30 ]; then
            echo "[entrypoint] database never became ready — aborting" >&2
            exit 1
        fi
        sleep 2
    done

    echo "[entrypoint] applying migrations (flask db upgrade)..."
    flask db upgrade
    echo "[entrypoint] migrations OK"
fi

exec "$@"
