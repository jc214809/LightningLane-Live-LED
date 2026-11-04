import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("disney-lll")

# Determine the base directory path dynamically. When installed via pip this
# resolves under site-packages, which a non-root/unwritable install (e.g. a
# plugin consumer) may not be able to write into -- see the fallback below.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the logs directory path. Tests override this (LLL_LOG_DIR) so pytest
# runs never interleave with a live app's real logs/app.log.
LOG_DIR = os.environ.get('LLL_LOG_DIR') or os.path.join(BASE_DIR, 'logs')

# Create handlers for both console and file
console_handler = logging.StreamHandler()  # For console output
logger.addHandler(console_handler)

# File logging is best-effort: a package installed under a read-only or
# unwritable location (e.g. site-packages of a consuming plugin) must not
# crash on import just because it can't create its own log file there.
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'app.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=10
    )
except OSError:
    fallback_dir = os.path.join(tempfile.gettempdir(), 'lightninglane-live-led-logs')
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(fallback_dir, 'app.log'),
            maxBytes=5 * 1024 * 1024,
            backupCount=10
        )
    except OSError:
        file_handler = None
        logger.addHandler(logging.NullHandler())
        logger.warning(
            "Could not create a log file under %s or %s; file logging disabled, console only.",
            LOG_DIR, fallback_dir,
        )

# Create a formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(funcName)s - %(message)s')
console_handler.setFormatter(formatter)
if file_handler is not None:
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logger.propagate = False

info = logger.info

warning = logger.warning

error = logger.error

log = logger.debug

exception = logger.exception
