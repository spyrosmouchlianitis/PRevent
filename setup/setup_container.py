import os
import logging
from typing import Any
from contextlib import redirect_stderr
from src.config import rewrite_setting
from src.secret_manager import get_secret
from setup.secret_managers.configure_cli import manage_secret_manager_dependency


def attempt_secret(secret: str) -> Any:
    try:
        with open(os.devnull, 'w') as hide, redirect_stderr(hide):
            return get_secret(secret)
    except Exception:
        return ''

# Write the values locally to avoid unnecessary repeated remote fetching
for secret in ['SECRET_MANAGER', 'PR_BLOCK', 'FP_STRICT', 'WEBHOOK_PORT', 'JWT_EXPIRY_SECONDS']:
    value = attempt_secret(secret)
    if value:
        rewrite_setting(secret, value)

try:
    manage_secret_manager_dependency(get_secret('SECRET_MANAGER'))
except Exception as e:
    logging.error(e)
