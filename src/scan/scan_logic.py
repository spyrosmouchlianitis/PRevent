from flask import current_app
from github import Repository, PullRequest
from typing import List, Dict, Tuple, Optional
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


def run_scan(changed_files: List[Dict[str, str]]) -> DetectionType:
    """
    Scan changed files and return only the first detection to avoid spamming the PR.
    Infected code indicates active compromise and should be addressed immediately,
    not get listed and orchestrated like vulnerabilities.
    """
    for file in changed_files:
        detection, additions_list = get_first_detection(file)
        if additions_list is None:
            continue
        if detection := handle_detection(file, detection, additions_list):
            return detection


def get_first_detection(
        file: Dict[str, str]
) -> Tuple[Optional[DetectionType], Optional[List[Tuple[int, str]]]]:
    filename = file['filename']
    ext = filename.split('.')[-1] if '.' in filename else None
    lang = extensions.get(ext, '')
    if not lang:
        return None, None
    
    additions_list = process_diff(file['diff'], lang)
    if not additions_list:
        return None, None

    extra_obfuscation_detectors = [
        detect_space_hiding,
        detect_encoded,
        detect_homoglyph
    ]

    if result := detect_dynamic_execution_and_obfuscation(file['full_content'], lang):
        return result, additions_list
    elif result := detect_executable(filename, file['full_content']):
        return result, additions_list
    else:
        for detector in extra_obfuscation_detectors:
            if result := detector(file['full_content']):
                return result, additions_list


def handle_detection(
    file: Dict[str, str],
    detection: DetectionType,
    additions_list: List[tuple]
) -> Dict:
    # TODO: Instead of filtering them out of the results, don't run them.
    if FP_STRICT and detection['severity'] != 'ERROR':
        return {}

    # Whole updated file is scanned, report only detections in additions (minimize FP noise).
    match = get_line_from_code(file['full_content'], detection['line_number'])
    if any(new_code[1] in match for new_code in additions_list):
        return {"filename": file['filename'], **detection}
    return {}


def get_line_from_code(code: str, line_number: int) -> str:
    lines = code.split('\n')
    if not (0 < line_number <= len(lines)):
        raise IndexError("Line number out of range")
    return lines[line_number - 1]
