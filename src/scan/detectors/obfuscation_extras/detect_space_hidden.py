from typing import List, Dict, Any


def detect_space_hiding(patch: str, lang: str) -> List[Dict[str, Any]]:
    found = []
    lines = patch.split('\n')
    for idx, line in enumerate(lines):
        if len(line) > 200 and ' ' * 200 in line:
            line_content = line.replace('  ', '')
            if len(line_content) > 50:
                found.append({
                    "detection": "Detected an unreasonable amount of spaces in line, probably for hiding",
                    "match": line_content[:100],
                    "line_number": idx + 1
                })
    return found
