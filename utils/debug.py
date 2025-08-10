import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("disney-lll")

# Determine the base directory path dynamically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Adjust according to your project's structure

# Define the logs directory path
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure the directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create handlers for both console and file
console_handler = logging.StreamHandler()  # For console output
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=5 * 1024 * 1024,
    backupCount=10
)

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
