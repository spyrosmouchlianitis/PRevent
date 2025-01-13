import re
import base64
from typing import List, Dict, Any
from cryptography.fernet import Fernet


def detect_encoded(patch: str, lang: str) -> List[Dict[str, Any]]:
    found = []
    lines = patch.splitlines()
    for line_number, line in enumerate(lines, start=1):
        encoded = [
            detection for results in [
                detect_b64(line, line_number),
                detect_b32(line, line_number),
                detect_hex(line, line_number),
                detect_unicode(line, line_number)
            ] for detection in results
        ]
        found.extend(encoded)
        found.extend(detect_fernet(patch))
    return found


def detect_b64(line: str, line_number: int) -> List[Dict[str, Any]]:
    found = []
    pattern = r'(?:(?:[\'\"\`])([A-Za-z0-9+/]{28,}={0,2})(?:[\'\"\`]))'
    for match in re.finditer(pattern, line):
        payload = match.group(1)
        if len(payload) % 4 == 0:
            try:
                decoded = base64.b64decode(payload).decode('utf-8')
                if decoded:
                    found.append({
                        "detection": "A hardcoded base64 encoded string.",
                        "severity": "WARNING",
                        "line_number": line_number,
                        "match": payload,
                        "decoded": decoded
                    })
            except:  # Ignore FP
                pass
    return found


def detect_b32(line: str, line_number: int) -> List[Dict[str, Any]]:
    found = []
    pattern = r'[^A-Za-z0-9]([A-Z2-7]{8,}(?:={4}|={6}|))[^A-Za-z0-9]'
    for match in re.finditer(pattern, line):
        payload = match.group(1)
        if len(payload.split('=')[0]) % 8 == 0:
            try:
                decoded = base64.b32decode(payload).decode('utf-8')
                if decoded:
                    found.append({
                        "detection": "A hardcoded base32 encoded string.",
                        "severity": "WARNING",
                        "line_number": line_number,
                        "match": payload,
                        "decoded": decoded
                    })
            except:  # Ignore FP
                pass
    return found


def detect_hex(line: str, line_number: int) -> List[Dict[str, Any]]:
    found = []
    pattern = r'((?:[0|\\][xX][0-9a-fA-F]{8,})+)'
    for match in re.finditer(pattern, line):
        payload = match.group(1)
        try:
            decoded = bytes.fromhex(payload[2:]).decode('utf-8')
        except:
            # This never fails, and some hex payloads are not trivial
            decoded = bytes(payload, 'utf-8').decode('unicode_escape')
        if decoded:
            found.append({
                "detection": "A hardcoded hex encoded string.",
                "severity": "WARNING",
                "line_number": line_number,
                "match": payload,
                "decoded": decoded
            })
    return found


def detect_unicode(line: str, line_number: int) -> List[Dict[str, Any]]:
    found = []
    pattern = r'((?:\\[uU][0-9A-Fa-f]{4})+)'
    for match in re.finditer(pattern, line):
        payload = match.group(1)
        try:
            decoded = bytes(payload, 'utf-8').decode('unicode_escape')
            if decoded:
                found.append({
                    "detection": "A hardcoded unicode encoded string.",
                    "severity": "WARNING",
                    "line_number": line_number,
                    "match": payload,
                    "decoded": decoded
                })
        except:  # Ignore FP
            pass
    return found


def detect_fernet(patch: str) -> List[Dict[str, Any]]:
    found = []
    pattern_payload = r'gAAAA[A-Za-z0-9_\-]+=+'
    for p_match in re.finditer(pattern_payload, patch):
        pattern_key = r"b'[A-Za-z0-9_-]{43}='"
        key_matches = re.findall(pattern_key, patch)
        for k_match in list(set(key_matches)):
            try:
                key_bytes = k_match[2:-1].encode('ascii')
                payload = p_match.group(1)
                decoded = Fernet(key_bytes).decrypt(payload).decode('utf-8')
                if decoded:
                    found.append({
                        "detection": "A hardcoded Fernet encoded string.",
                        "severity": "WARNING",
                        "line_number": patch[:p_match.start()].count('\n') + 1,
                        "match": payload,
                        "decoded": decoded
                    })
            except:  # Ignore FP
                continue
    return found
