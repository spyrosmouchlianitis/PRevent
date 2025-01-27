from github import Repository, PullRequest
from src.utils.github import comment_detection
from src.scan.languages import extensions
from src.scan.detectors.utils import DetectionType
from src.settings import FP_STRICT


def get_lang(filename: str) -> tuple[str, str]:
    ext = filename.split('.')[-1] if '.' in filename else None
    return ext, extensions.get(ext, '')


def get_loc(code: str, line_number: int) -> str:
    lines = code.split('\n')
    if not (0 < line_number <= len(lines)):
        raise IndexError("Line number out of range")
    return lines[line_number - 1]


def handle_one_liners(
    additions_list: list[tuple[int, str]],
    filename: str,
    repo: Repository,
    pr: PullRequest
) -> bool:
    for addition in additions_list:
        if len(addition[1]) > 400:
            if not FP_STRICT:
                detection: DetectionType = {
                    "filename": filename,
                    "line_number": addition[0],
                    "severity": "INFO",
                    "message": "Including minified single-line files or similar in a codebase is discouraged, "
                                "because code should be readable. "
                                "'Unreadability' is a central indication of malicious code. "
                                "currently, such files are excluded from this scan. "
                                "It's recommended to store them in a CDN or a storage service."
                }
                comment_detection(detection, repo, pr)
            return True
    return False
