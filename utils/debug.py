import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("disney-lll")

# Create handlers for both console and file
console_handler = logging.StreamHandler()  # For console output
file_handler = RotatingFileHandler('./logs/app.log', maxBytes=5 * 1024 * 1024, backupCount=10)  # 5 MB max size, keep 5 backups

# Create a formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(funcName)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.propagate = False

info = logger.info

warning = logger.warning

error = logger.error

log = logger.debug

exception = logger.exception
