import os
import shutil
import subprocess
import tempfile
from flask import current_app
from typing import TypedDict, Optional
from src.settings import RULESET_REPO
from src.config import get_app_root


# Keep it minimal to avoid repeating line matching and filenames handling
class DetectionType(TypedDict, total=False):
    message: str
    severity: str
    line_number: int
    decoded: Optional[str]   # For encodings detectors
    match: Optional[str]     # Add in handler (derived from line_number)
    filename: Optional[str]  # Add in handler


def get_ruleset_dir():
    if not is_git_installed():
        return

    root_path = get_app_root()
    path = 'src/scan/detectors'
    ruleset_dir = f'{root_path}/{path}/malicious-code-ruleset'

    try:
        if not os.path.exists(ruleset_dir):
            clone_repo(RULESET_REPO, ruleset_dir)
        else:
            fetch_repo(ruleset_dir)
            if has_new_commits(ruleset_dir):
                pull_repo(ruleset_dir, RULESET_REPO)

        return ruleset_dir

    except subprocess.CalledProcessError:
        current_app.logger.error(
            f"No internet connection or error fetching ruleset from {RULESET_REPO} . "
            "Using local version."
        )
        offline_ruleset_dir = f'{root_path}/{path}/offline-ruleset-copy'
        return offline_ruleset_dir


def is_git_installed() -> bool:
    if shutil.which('git'):
        return True
    current_app.logger.error("Git is not installed or not found in the PATH.")
    return False


def clone_repo(repo: str, destination_path: str) -> None:
    subprocess.run(['git', 'clone', repo, destination_path], check=True)
    current_app.logger.info(f"Cloned repository from {repo}.")


def fetch_repo(repo_path: str) -> None:
    subprocess.run(['git', 'fetch', 'origin'], cwd=repo_path, check=True)


def has_new_commits(repo_path: str) -> bool:
    result = subprocess.run(
        ['git', 'rev-list', '--count', 'HEAD..origin/main'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return result.stdout and int(result.stdout.strip()) > 0


def pull_repo(repo_path: str, repo_url: str) -> None:
    subprocess.run(['git', 'pull', 'origin', 'main'], cwd=repo_path, check=True)
    current_app.logger.info(f"Pulled latest changes from the {repo_url}.")


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
