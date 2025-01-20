import json
from flask import current_app
from github import Repository, PullRequest
from typing import Optional
from src.scan.detectors.utils import DetectionType
from src.scan.languages import extensions
from src.utils.patch import process_diff
from src.scan.detectors.run_semgrep import detect_dynamic_execution_and_obfuscation
from src.scan.detectors.obfuscation_extras.detect_encoded import detect_encoded
from src.scan.detectors.obfuscation_extras.detect_executable import detect_executable
from src.scan.detectors.obfuscation_extras.detect_space_hidden import detect_space_hiding
from src.scan.detectors.obfuscation_extras.detect_homoglyph import detect_homoglyph
from src.utils.github import get_changed_files, determine_scan_status, create_commit_status
from src.settings import APP_REPO, FP_STRICT


def handle_scan(
    repo: Repository,
    pr: PullRequest,
    commit_sha: str
) -> str:
    # "success" status if no files were changed
    status = "success"

    # Get full files for proper code analysis. PR contains only diffs.
    changed_files = get_changed_files(repo, pr)
    if changed_files:
        scan_results = run_scan(changed_files)
        current_app.logger.info(f"Scanned PR #{pr.number}")
        status, description, comment = determine_scan_status(scan_results, pr, repo)
        target_url = comment.html_url if hasattr(comment, 'html_url') else APP_REPO
        create_commit_status(repo, commit_sha, status, description, target_url)

    return status


def run_scan(changed_files: list[dict[str, str]]) -> Optional[DetectionType]:
    """
    Scan changed files and return only the first detection to avoid spamming the PR.
    Infected code indicates active compromise and should be addressed immediately,
    not get listed and orchestrated like vulnerabilities.
    """
    for file in changed_files:
        if not all(key in file for key in ['filename', 'diff', 'full_content']):
            raise ValueError(f"File must contain 'filename', 'diff' and 'full_content': {json.dumps(file)}")

        extension, language = get_lang(file['filename'])
        if not language:
            return None

        additions_list = process_diff(file['diff'], language)
        if not additions_list:
            continue

        detection: DetectionType = get_first_detection(file, extension)

        if full_detection_data := enrich_detection(file, detection, additions_list):
            return full_detection_data


def get_lang(filename: str) -> tuple[str, str]:
    ext = filename.split('.')[-1] if '.' in filename else None
    return ext, extensions.get(ext, '')


def get_first_detection(
    file: dict[str, str],
    extension: str
) -> Optional[dict]:

    extra_obfuscation_detectors = [
        (detect_space_hiding, "ERROR"),
        (detect_encoded, "WARNING"),
        (detect_homoglyph, "WARNING")
    ]

    if result := detect_dynamic_execution_and_obfuscation(file['full_content'], extension):
        return result

    elif result := detect_executable(file['filename'], file['full_content']):
        return result

    else:
        for detector in extra_obfuscation_detectors:
            if not FP_STRICT or (FP_STRICT and detector[1] == "ERROR"):
                if result := detector[0](file['full_content']):
                    return {
                        "severity": detector[1],
                        **result
                    }
    return None


def enrich_detection(
    file: dict[str, str],
    detection: DetectionType,
    additions_list: list[tuple]
) -> Optional[DetectionType]:

    # Derived from the detector's nature, a match key may or may not be present.
    # Also helps with Semgerp placing the match field behind an auth wall.
    match = detection.get('match') or get_loc(file['full_content'], detection['line_number'])
    
    # Whole updated file is scanned, report only detections in additions.
    if any(new_code[1] in match for new_code in additions_list):
        return {
            "filename": file['filename'],
            **detection,
            "match": match.replace('  ', '')
        }
    return None


def get_loc(code: str, line_number: int) -> str:
    lines = code.split('\n')
    if not (0 < line_number <= len(lines)):
        raise IndexError("Line number out of range")
    return lines[line_number - 1]
