from src.scan.detectors.utils import DetectionType


def detect_space_hiding(patch: str) -> DetectionType:
    lines = patch.split('\n')
    for idx, line in enumerate(lines):
        if len(line) > 200 and ' ' * 200 in line:
            line_content = line.replace('  ', '')
            if len(line_content) > 50:
                return {
                    "message": "An unreasonable amount of spaces in line, probably for hiding",
                    "severity": "ERROR",
                    "line_number": idx + 1,
                    "match": line_content[:100]
                }
