import multiprocessing

# Server socket
bind = "127.0.0.1:8081"
workers = multiprocessing.cpu_count() * 2 + 1
# Keep slow client sockets from consuming an entire process pool. Public
# traffic should enter through the nginx configuration in deploy/, which adds
# the actual header/body read timeouts.
worker_class = 'gthread'
threads = 4
timeout = 900

# Worker settings
max_requests = 1000
max_requests_jitter = 50
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'spotify-ytm-api'

# Production settings
reload = False
preload_app = True
