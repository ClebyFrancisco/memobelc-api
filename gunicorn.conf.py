# gunicorn.conf.py
import multiprocessing
import os

# Workers: 2-4 workers é bom para começar
# Fórmula: (2 x $num_cores) + 1
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))

# Worker class - gthread é bom para I/O bound (API com DB)
worker_class = 'gthread'

# Threads por worker - 2-4 threads é ideal para APIs
threads = int(os.environ.get('GUNICORN_THREADS', '4'))

# Bind
bind = '0.0.0.0:5000'

# Timeout (30s é padrão, aumentar se tiver operações longas)
timeout = 120

# Graceful timeout
graceful_timeout = 30

# Keep alive
keepalive = 5

# Logging
accesslog = '-'  # Stdout
errorlog = '-'   # Stderr
loglevel = 'info'

# Worker restart (previne memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Pre-load da app (economiza memória)
preload_app = True