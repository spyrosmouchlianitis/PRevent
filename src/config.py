import os
import logging
from logging.handlers import RotatingFileHandler
from src.settings import INFO_LOG_FILE, ERROR_LOG_FILE


def configure_logging(app) -> None:
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

    # Rotating file handler
    file_handler = RotatingFileHandler(INFO_LOG_FILE, maxBytes=10_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Error-level handler
    error_handler = RotatingFileHandler(ERROR_LOG_FILE, maxBytes=10_000_000, backupCount=5)
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # Add handlers to the app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)


def get_app_root() -> str:
    current_dir = os.path.dirname(__file__)
    while current_dir != os.path.dirname(current_dir):  # Loop until we reach the root dir
        if os.path.exists(os.path.join(current_dir, 'pyproject.toml')):  # Root marker
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return current_dir


def rewrite_setting(setting_name: str, new_value: str) -> None:
    file_path = f'{get_app_root()}/src/settings.py'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        found = False

        for line in lines:
            if line.startswith(setting_name):
                f.write(f"{setting_name} = {new_value}\n")
                found = True
            else:
                f.write(line)

        if not found:
            f.write(f"\n{setting_name} = {new_value}\n")


def write_setting(setting_name: str, new_value: str) -> None:
    file_path = f'{get_app_root()}/src/settings.py'
    with open(file_path, 'a') as file:
        file.write(f"{setting_name} = {new_value}\n")
