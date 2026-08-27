"""
Gunicorn configuration — self-documenting via env vars so compose needs no
CLI flags. Loaded automatically by gunicorn from the project root.

Reference: https://docs.gunicorn.org/en/stable/settings.html
"""
import multiprocessing
import os

# تعداد ورکرها: WEB_CONCURRENCY (کانونی‌ترین نام env بین PaaSها) وگرنه 2×CPU
_workers = os.environ.get('WEB_CONCURRENCY')
workers: int = int(_workers) if _workers else max(2, (multiprocessing.cpu_count() or 2) * 2)

bind: str = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# تایم‌آوت: درگاه‌های بانکی/SMTP گاهی کندند؛ ۳۰ ثانیهٔ پیش‌فرض کم است
timeout: int = int(os.environ.get('GUNICORN_TIMEOUT', '120'))
graceful_timeout: int = 30
keepalive: int = 5

# چرخش منظم ورکر — محافظت در برابر نشتی حافظهٔ انباشته در پروسه‌های طولانی
max_requests: int = int(os.environ.get('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter: int = 100

accesslog: str = '-'
errorlog: str = '-'
loglevel: str = os.environ.get('LOG_LEVEL', 'info').lower()

access_log_format: str = '%(h)s "%(r)s" %(s)s %(b)s "%(f)s" %(L)ss'
