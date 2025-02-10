import re
import base64
from cryptography import fernet
from src.settings import FULL_FINDINGS


def detect_encoded(patch: str) -> list[dict]:
    results = []
    for detector in [
        detect_fernet,
        detect_b64,
        detect_unicode,
        detect_hex
    ]:
        if detector_results := detector(patch):
            results.extend(detector_results)
            if not FULL_FINDINGS:
                return results
    return results


def detect_b64(patch: str) -> list[dict]:
    results = []
    pattern = re.compile(r'[\'\"`]([A-Za-z0-9+/]{12,}={0,2})[\'\"`]')
    for match in pattern.finditer(patch):
        payload = match.group(1)
        if len(payload) % 4 == 0:
            try:
                decoded = base64.b64decode(payload).decode('utf-8')
                if decoded and len(decoded) > 3:
                    results.append({
                        "message": "A hardcoded base64 encoded string. Either malicious or a bad practice. "
                                   "(Set \"FP_STRICT = False\" to disable)",
                        "line_number": get_match_line_number(match, patch),
                        "decoded": decoded
                    })
                    if not FULL_FINDINGS:
                        return results
            except (ValueError, UnicodeDecodeError):
                continue  # Ignore FP
    return results


def detect_hex(patch: str) -> list[dict]:
    results = []
    pattern = re.compile(r'((?:[0\\][xX][0-9a-fA-F]{8,})+)')
    for match in pattern.finditer(patch):
        payload = match.group(1).replace('\\\\', '\\')
        if len(payload) >= 16:

            try:
                decoded = bytes.fromhex(payload[2:]).decode('utf-8')

            # Handle non-trivial hex payloads
            except (ValueError, UnicodeDecodeError):
                decoded = bytes(payload, 'utf-8').decode('unicode_escape')

            if (
                (decoded.count('0x') >= 2 or decoded.count('\\x') >= 2)
                and len(decoded) >= 16
            ) or (
                '0x' not in decoded
                and '\\x' not in decoded
                and len(decoded) > 3
            ):
                results.append({
                    "message": "A hardcoded hex encoded string. Either malicious or a bad practice. "
                               "(Set \"FP_STRICT = False\" to disable)",
                    "line_number": get_match_line_number(match, patch),
                    "decoded": decoded
                })
                if not FULL_FINDINGS:
                    return results
    return results


def detect_unicode(patch: str) -> list[dict]:
    results = []
    pattern = re.compile(r'((?:\\[uU][0-9A-Fa-f]{4})+)')
    for match in pattern.finditer(patch):
        payload = match.group(1).replace('\\\\', '\\')
        if len(payload) >= 24:
            try:
                decoded = bytes(payload, 'utf-8').decode('unicode_escape')
                if (
                    decoded
                    and '\\u' not in decoded
                    and len(decoded) > 3
                ):
                    results.append({
                        "message": "A hardcoded unicode encoded string. Either malicious or a bad practice. "
                                   "(Set \"FP_STRICT = False\" to disable)",
                        "line_number": get_match_line_number(match, patch),
                        "decoded": decoded
                    })
                    if not FULL_FINDINGS:
                        return results
            except (UnicodeDecodeError, TypeError):
                continue  # Ignore FP
    return results


def detect_fernet(patch: str) -> list[dict]:
    results = []
    pattern_payload = re.compile(r'gAAAA[A-Za-z0-9_\-]+=+')
    for p_match in pattern_payload.finditer(patch):
        pattern_key = re.compile(r"b'[A-Za-z0-9_-]{43}='")
        key_matches = pattern_key.findall(patch)
        for k_match in list(set(key_matches)):
            try:
                key_bytes = k_match[2:-1].encode('ascii')
                payload = p_match.group()
                decoded = fernet.Fernet(key_bytes).decrypt(payload).decode('utf-8')
                if decoded:
                    results.append({
                        "message": "A hardcoded Fernet encoded string.",
                        "line_number": patch[:p_match.start()].count('\n') + 1,
                        "decoded": decoded
                    })
                    if not FULL_FINDINGS:
                        return results
            except fernet.InvalidToken:
                continue  # Ignore FP
    return results


def get_match_line_number(match: re.Match, patch: str) -> int:
    index = match.start()
    return patch.count('\n', 0, index) + 1
