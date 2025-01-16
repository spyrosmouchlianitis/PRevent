import os
import shutil
import subprocess
import tempfile
from flask import current_app
from typing import TypedDict
from src.scan.languages import major
from src.settings import RULESET_REPO
from src.config import get_app_root


class DetectionType(TypedDict, total=True):
    message: str
    severity: str
    line_number: int


def get_ruleset_dir():

    if not shutil.which('git'):
        current_app.logger.error("Git is not installed or not found in the PATH.")
        return
    
    root_path = get_app_root()
    path = 'src/scan/detectors'
    try:
        ruleset_dir = f'{root_path}/{path}/malicious-code-ruleset'

        if not os.path.exists(ruleset_dir):
            subprocess.run(['git', 'clone', RULESET_REPO, ruleset_dir], check=True)
            current_app.logger.info(f"Cloned repository from {RULESET_REPO}.")
        else:
            # Fetch latest changes
            subprocess.run(['git', 'fetch', 'origin'], cwd=ruleset_dir, check=True)
            
            # Quickly check if local is behind
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD..origin/main'],
                cwd=ruleset_dir,
                capture_output=True,
                text=True
            )
            if result.stdout and int(result.stdout.strip()) > 0:
                subprocess.run(['git', 'pull', 'origin', 'main'], cwd=ruleset_dir, check=True)
                current_app.logger.info(f"Pulled latest changes from the {RULESET_REPO}.")

        return ruleset_dir
    
    except subprocess.CalledProcessError:
        current_app.logger.error(
            f"No internet connection or error fetching ruleset from {RULESET_REPO} . "
            "Using local version."
        )
        offline_ruleset_dir = f'{root_path}/{path}/offline-ruleset-copy'
        return offline_ruleset_dir


def get_file_extension(lang: str) -> str:
    return next((key for key, val in major.items() if val == lang), '')


def create_temp_file(code_string: str, extension: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, mode='w', suffix=f'.{extension}'
        ) as temp_file:
            temp_file.write(code_string)
            temp_file.close()
            return temp_file.name
        
    except (OSError, IOError) as e:
        current_app.logger.error(f"Failed to create temporary file: {e}")
        return ''
