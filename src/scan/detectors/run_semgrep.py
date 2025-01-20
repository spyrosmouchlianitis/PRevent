import os
import json
import random
import subprocess
from flask import current_app
from typing import Optional, Any
from src.scan.detectors.utils import DetectionType
from src.scan.detectors.utils import (
    get_ruleset_dir,
    create_temp_file
)
from src.settings import FP_STRICT


def detect_dynamic_execution_and_obfuscation(
    code_string: str,
    extension: str
) -> Optional[DetectionType]:
    """
    Analyzes code for dynamic execution and obfuscation patterns using Semgrep.
    Save scanned code to a temporary file, remove it in the end.
    """
    findings = None
    temp_file_path = create_temp_file(code_string, extension)
    if temp_file_path and os.path.exists(temp_file_path):
        findings = run_semgrep(temp_file_path)["results"]
        os.remove(temp_file_path)
    if findings:
        return process_semgrep_finding(random.choice(findings))
    return None


def run_semgrep(temp_file_path: str) -> Optional[dict[str, Any]]:
    try:
        ruleset_dir = get_ruleset_dir()
        command = [
            'semgrep',
            '--config', ruleset_dir,
            '--metrics', 'off',
            '--quiet',
            '--json',
            temp_file_path
        ]
        if FP_STRICT:
            command.extend(['--severity', 'error'])

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stdout:  # Monitor Semgrep output in real-time
            if line.strip():
                result = json.loads(line)
                process.terminate()  # Stop the scan after the first result
                return result

        process.wait()  # Clean termination
        return None

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Semgrep failed: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Semgrep output: {str(e)}")


def process_semgrep_finding(finding: dict) -> Optional[DetectionType]:
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
