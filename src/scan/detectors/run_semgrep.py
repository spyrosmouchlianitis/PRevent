import os
import json
import random
import subprocess
from flask import current_app
from typing import Optional, Dict, Any
from src.scan.detectors.utils import DetectionType
from src.scan.detectors.utils import (
    get_ruleset_dir,
    get_file_extension,
    create_temp_file
)
from src.settings import FP_STRICT


def detect_dynamic_execution_and_obfuscation(
    code_string: str,
    lang: str
) -> Optional[DetectionType]:
    """
    Analyzes code for dynamic execution and obfuscation patterns using Semgrep.
    Save scanned code to a temporary file, remove it in the end.
    """
    findings = None
    extension = get_file_extension(lang)
    if extension:
        temp_file_path = create_temp_file(code_string, extension)
        if temp_file_path and os.path.exists(temp_file_path):
            findings = run_semgrep(temp_file_path)["results"]
            os.remove(temp_file_path)
    if findings:
        return process_semgrep_finding(random.choice(findings))
    return None


def run_semgrep(temp_file_path: str) -> Dict[str, Any]:
    try:
        ruleset_dir = get_ruleset_dir()

        command = [
            'semgrep', '--config', ruleset_dir, '--metrics', 'off', '--json', temp_file_path
        ]
        if FP_STRICT:
            command.extend(['--severity', 'error'])

        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True
        )
        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Semgrep failed: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Semgrep output: {str(e)}")


def process_semgrep_finding(finding: Dict) -> Optional[DetectionType]:
    try:
        return {
            "message": finding["extra"]["message"],
            "severity": finding["extra"]["severity"],
            "line_number": int(finding["start"]["line"])
        }
    except KeyError as e:
        current_app.logger.error(
            f"Missing expected key in Semgrep result: {e}\n{finding}"
        )
        return None
