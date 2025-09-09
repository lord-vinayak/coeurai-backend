import os
# The address and port to bind to
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# The number of worker processes
workers = 2

# The timeout for workers
timeout = 120