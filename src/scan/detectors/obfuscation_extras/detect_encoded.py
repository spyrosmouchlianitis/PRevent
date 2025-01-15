import re
import base64
from cryptography.fernet import Fernet
from src.scan.detectors.utils import DetectionType


def detect_encoded(patch: str) -> DetectionType:
    for line_number, line in enumerate(patch.splitlines(), start=1):
        for detector in [
            detect_fernet,
            detect_b64,
            detect_b32,
            detect_unicode,
            detect_hex
        ]:
            if (result := detector(line, line_number)):
                return result
    return {}


def detect_b64(line: str, line_number: int) -> DetectionType:
    pattern = r'(?:(?:[\'\"\`])([A-Za-z0-9+/]{12,}={0,2})(?:[\'\"\`]))'
    for match in re.finditer(pattern, line):
        payload = match.group(1)
        if len(payload) % 4 == 0:
            try:
                decoded = base64.b64decode(payload).decode('utf-8')
                if decoded and len(decoded) > 3:
                    return {
                        "message": "A hardcoded base64 encoded string.",
                        "severity": "WARNING",
                        "line_number": line_number,
                        "match": payload,
                        "decoded": decoded
                    }
            except:  # Ignore FP
                pass


def detect_b32(line: str, line_number: int) -> DetectionType:
    pattern = r'(?:(?:[\'\"\`])([A-Z2-7]{8,}(?:={4}|={6}|))(?:[\'\"\`]))'
    for match in re.finditer(pattern, line):
        payload = match.group(1)
        if len(payload.split('=')[0]) % 8 == 0:
            try:
                decoded = base64.b32decode(payload).decode('utf-8')
                if decoded and '\\u' not in decoded and len(decoded) > 3:
                    return {
                        "message": "A hardcoded base32 encoded string.",
                        "severity": "WARNING",
                        "line_number": line_number,
                        "match": payload,
                        "decoded": decoded
                    }
            except:  # Ignore FP
                pass


def detect_hex(line: str, line_number: int) -> DetectionType:
    pattern = r'((?:[0|\\][xX][0-9a-fA-F]{8,})+)'
    for match in re.finditer(pattern, line):
        payload = match.group(1).replace('\\\\', '\\')
        if len(payload) >= 16:
            try:
                decoded = bytes.fromhex(payload[2:]).decode('utf-8')
            except:
                # This never fails, while handling non-trivial hex payloads
                decoded = bytes(payload, 'utf-8').decode('unicode_escape')
            if (
                (decoded.count('0x') >= 2 or decoded.count('\\x') >= 2) and len(decoded) >= 16
            ) or (
                '0x' not in decoded and '\\x' not in decoded and len(decoded) > 3
            ):
                return {
                    "message": "A hardcoded hex encoded string.",
                    "severity": "WARNING",
                    "line_number": line_number,
                    "match": payload,
                    "decoded": decoded
                }


def detect_unicode(line: str, line_number: int) -> DetectionType:
    pattern = r'((?:\\[uU][0-9A-Fa-f]{4})+)'
    for match in re.finditer(pattern, line):
        payload = match.group(1).replace('\\\\', '\\')
        if len(payload) >= 24:
            try:
                decoded = bytes(payload, 'utf-8').decode('unicode_escape')
                if (
                    decoded
                    and (('\\u' not in decoded and len(decoded) > 3)
                         or len(match) >= 24)
                ):
                    return {
                        "message": "A hardcoded unicode encoded string.",
                        "severity": "WARNING",
                        "line_number": line_number,
                        "match": payload,
                        "decoded": decoded
                    }
            except:  # Ignore FP
                pass


def detect_fernet(patch: str) -> DetectionType:
    pattern_payload = r'gAAAA[A-Za-z0-9_\-]+=+'
    for p_match in re.finditer(pattern_payload, patch):
        pattern_key = r"b'[A-Za-z0-9_-]{43}='"
        key_matches = re.findall(pattern_key, patch)
        for k_match in list(set(key_matches)):
            try:
                key_bytes = k_match[2:-1].encode('ascii')
                payload = p_match.group()
                decoded = Fernet(key_bytes).decrypt(payload).decode('utf-8')
                if decoded:
                    return {
                        "message": "A hardcoded Fernet encoded string.",
                        "severity": "WARNING",
                        "line_number": patch[:p_match.start()].count('\n') + 1,
                        "match": payload,
                        "decoded": decoded
                    }
            except:  # Ignore FP
                continue
