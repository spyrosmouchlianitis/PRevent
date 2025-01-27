import os
import json
import concurrent.futures
from flask import current_app
from github import Repository, PullRequest
from typing import Optional, Callable
from src.scan.detectors.utils import DetectionType
from src.utils.patch import process_diff
from src.scan.detectors.run_semgrep import detect_dynamic_execution_and_obfuscation
from src.scan.detectors.obfuscation_extras.detect_encoded import detect_encoded
from src.scan.detectors.obfuscation_extras.detect_executable import detect_executable
from src.scan.detectors.obfuscation_extras.detect_space_hidden import detect_space_hiding
from src.scan.detectors.obfuscation_extras.detect_homoglyph import detect_homoglyph
from src.scan.utils import (
    get_lang,
    get_loc,
    handle_one_liners
)
from src.utils.github import (
    get_changed_files,
    determine_scan_status,
    create_commit_status
)
from src.settings import APP_REPO, FP_STRICT, FULL_FINDINGS


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
        scan_results: list = run_scan(changed_files, repo, pr)
        current_app.logger.info(f"Scanned PR #{pr.number}")
        status, description, comment = determine_scan_status(scan_results, pr, repo)
        target_url = comment.html_url if hasattr(comment, 'html_url') else APP_REPO
        create_commit_status(repo, commit_sha, status, description, target_url)

    return status


def run_scan(
    changed_files: list[dict[str, str]],
    repo: Repository,
    pr: PullRequest
) -> list[DetectionType]:
    """
    Scan changed files and return only the first detection to avoid spamming the PR.
    Infected code indicates active compromise and should be addressed immediately,
    not get listed and orchestrated like vulnerabilities.
    """
    for file in changed_files:
        if not all(key in file for key in ['filename', 'diff', 'full_content']):
            raise ValueError(f"File must contain 'filename', 'diff' and 'full_content': {json.dumps(file)}")

        filename = file['filename']
        extension, language = get_lang(filename)
        if not language:
            return []

        additions_list = process_diff(file['diff'], language)
        if not additions_list:
            continue

        # Exclude minified files and other one-liners from the scan to avoid false-positives
        if handle_one_liners(additions_list, filename, repo, pr):
            continue

        detections: list[DetectionType] = get_detections(file, extension)

        results = []
        for detection in detections:
            if full_detection_data := enrich_detection(file, detection, additions_list):
                results.append(full_detection_data)
                if not FULL_FINDINGS:
                    return results
        return results


def get_detections(
    file: dict[str, str],
    extension: str
) -> list[dict]:
    full_content = file['full_content']

    detection_tasks = [
        (detect_dynamic_execution_and_obfuscation, (full_content, extension)),
        (detect_executable, (file['filename'], full_content)),
        *get_extra_detection_tasks(full_content)
    ]

    return run_detection_tasks(detection_tasks)


def get_extra_detection_tasks(
    full_content: str
) -> list[tuple[Callable, tuple]]:
    extra_obfuscation_detectors = [
        (detect_space_hiding, "ERROR"),
        (detect_encoded, "WARNING"),
        (detect_homoglyph, "WARNING")
    ]

    tasks = []

    # Add extra obfuscation detectors
    for detector, severity in extra_obfuscation_detectors:
        if FP_STRICT and severity != "ERROR":
            continue
        tasks.append((detector, (full_content,)))  # Pass as tuple for executor

    return tasks


def run_detection_tasks(tasks: list[tuple[Callable, tuple]]) -> list[dict]:
    # CPU-bound string processing. Semgrep is I/O bound, but runs as a single-command blackbox.
    if tasks:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                futures = [
                    executor.submit(task[0], *task[1]) for task in tasks
                ]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        results = future.result(timeout=5)
                        if results:
                            if not FULL_FINDINGS:
                                executor.shutdown(wait=False)
                            return results
                    except concurrent.futures.TimeoutError:
                        current_app.logger.error("Task timed out.")
        except Exception as e:
            current_app.logger.error(f"Detection process failed: {e}")
    return []


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
