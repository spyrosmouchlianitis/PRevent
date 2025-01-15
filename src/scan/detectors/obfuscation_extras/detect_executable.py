from src.scan.detectors.utils import DetectionType


def detect_executable(filename: str, patch: str) -> DetectionType:

    ext = filename.split('.')[-1].lower()

    windows = {
        'exe',
        'msi',
        'sys',
        'com',
        'cpl',
        'scr',
        'vxd',
        'ocx',
        'drv',
        'bpl',
        'efi'
    }

    mac = {
        'app',
        'dmg',
        'pkg',
        'kext',
        'command'
    }

    unix = {
        'bin',
        'run',
        'deb',
        'rpm',
        'out'
    }

    shared = {
        'dll',
        'so',
        'framework'
    }

    result_base = {
        "severity": "WARNING",
        "line_number": 1
    }

    if ext in windows | mac | unix | shared:
        return [{"message": f"An executable file: {ext}", **result_base}]

    magic_bytes = patch[:8].encode('utf-8')

    # ELF (Linux/Unix executables)
    if magic_bytes[:4] == b'\x7fELF':
        return [{"message": "An executable: ELF", **result_base}]

    # PE (Windows executables like .exe, .dll, .sys)
    if magic_bytes[:2] == b'MZ':
        return [{"message": "A Windows executable.", **result_base}]

    # macOS Disk Images (.dmg)
    if magic_bytes[:4] == b'koly':
        return [{"message": "An executable: dmg", **result_base}]

    # Debian packages (.deb)
    if magic_bytes[:4] == b'!<ar':
        return [{"message": "An executable: deb", **result_base}]

    # Red Hat packages (.rpm)
    if magic_bytes[:4] == b'\xed\xab\xee\xdb':
        return [{"message": "An executable: rpm", **result_base}]

    # EFI executables
    if magic_bytes[:2] == b'MZ':
        return [{"message": "An executable: EFI", **result_base}]

    # Self-contained Linux binaries (.bin, .run) - GZIP
    if magic_bytes[:2] == b'\x1f\x8b': 
        return [{"message": "An Linux executable.", **result_base}]

    # # JAR (and ZIP, APK)
    # if magic_bytes[:4] == b'PK\x03\x04': 
    #     return [{"message": "An executable archive", **result_base}
    
    return [{}]
