"""Compatibility shim: Pushover moved to utils/pushover.py so self_update no longer imports
settings_page. A board mid-update can still have a running process (the settings service, or the
old self_update) that imports the old path; this keeps it working. Remove it a release later.
"""

from utils.pushover import MESSAGES_URL, TIMEOUT_S, PushoverError, _errors, _reason, send, send_pin

__all__ = ["MESSAGES_URL", "TIMEOUT_S", "PushoverError", "_errors", "_reason", "send", "send_pin"]
