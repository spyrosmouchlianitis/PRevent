from flask import current_app
from typing import List, Dict, Any, Optional
from src.scan.languages import extensions
from src.utils.patch import process_diff
from src.scan.detectors.run_semgrep import detect_dynamic_execution_and_obfuscation
from src.scan.detectors.obfuscation_extras.detect_encoded import detect_encoded
from src.scan.detectors.obfuscation_extras.detect_executable import detect_executable
from src.scan.detectors.obfuscation_extras.detect_space_hidden import detect_space_hiding
from src.scan.detectors.obfuscation_extras.detect_homoglyph import detect_homoglyph
from src.utils.github import get_changed_files, determine_scan_status, create_commit_status
from src.settings import APP_REPO, FP_STRICT


def run_scan(changed_files: List[Dict[str, str]]) -> List[Dict]:
    results = []
    detectors = [
        detect_dynamic_execution_and_obfuscation,
        detect_encoded,
        detect_homoglyph,
        detect_space_hiding
    ]

    for file in changed_files:
        additions_list, detections = process_file(file, detectors)
        if additions_list is None:
            continue
        results.extend(filter_detections(file, detections, additions_list))

    return results


def process_file(file: Dict[str, str], detectors: List) -> Optional[tuple]:
    filename = file['filename']
    ext = filename.split('.')[-1] if '.' in filename else None
    lang = extensions.get(ext, '')
    if not lang:
        return None, None
    
    additions_list = process_diff(file['diff'], lang)
    if not additions_list:
        return None, None
    
    detections = aggregate_detector_results(file['full_content'], lang, detectors)
    executables = detect_executable(filename, file['full_content'])
    if executables:
        detections.append(executables)

    return additions_list, detections


def filter_detections(
    file: Dict[str, str],
    detections: List[Dict],
    additions_list: List[tuple]
) -> List[Dict]:
    results = []
    for result in detections:
        if FP_STRICT and result['severity'] != 'ERROR':
            continue
        match = get_line_from_code(file['full_content'], result['line_number'])
        if any(new_code[1] in match for new_code in additions_list):
            results.append({"filename": file['filename'], **result})
    return results


# TODO: Normalize output and remove this method
def aggregate_detector_results(
    file_content: str,
    lang: str,
    detectors: List
) -> List[Dict[str, Any]]:
    results = []
    for detector in detectors:
        output = detector(file_content, lang)
        if output:
            if isinstance(output, tuple):
                for sublist in output:
                    results.extend(sublist)
            elif isinstance(output, list):
                results.extend(output)
            elif isinstance(output, dict):
                results.append(output)

    return results


def handle_scan(repo, pr, commit_sha):
    # Get full files for proper code analysis. PR contains only diffs.
    changed_files = get_changed_files(repo, pr)
    scan_results = run_scan(changed_files)
    current_app.logger.info(f"Scanned PR #{pr.number}")
    status, description, comment = determine_scan_status(scan_results, pr, repo)
    target_url = comment.html_url if comment else APP_REPO
    create_commit_status(repo, commit_sha, status, description, target_url)


def get_line_from_code(code: str, line_number: int) -> str:
    lines = code.split('\n')
    if not (0 < line_number <= len(lines)):
        raise IndexError("Line number out of range")
    return lines[line_number - 1]
