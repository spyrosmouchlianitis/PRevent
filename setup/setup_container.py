import os
import logging
from typing import Any
from contextlib import redirect_stderr
from src.config import rewrite_setting
from src.secret_manager import get_secret
from src.validation.config import validate_config_parameters
from setup.secret_managers.configure_cli import manage_secret_manager_dependency


def attempt_secret(secret: str) -> Any:
    try:
        with open(os.devnull, 'w') as hide, redirect_stderr(hide):
            return get_secret(secret)
    except Exception:
        return ''


# Write the values locally to avoid unnecessary repeated remote fetching
for secret_key in [
    'SECRET_MANAGER',
    'BLOCK_PR',
    'FP_STRICT',
    'FULL_FINDINGS',
    'WEBHOOK_PORT',
    'JWT_EXPIRY_SECONDS'
]:
    value = attempt_secret(secret_key)
    if value:
        rewrite_setting(secret_key, value)

try:
    validate_config_parameters()
    if secret_manager := get_secret('SECRET_MANAGER'):
        manage_secret_manager_dependency(secret_manager)
except Exception as e:
    logging.error(e)
