import os
import json
import random
import subprocess
from flask import current_app
from typing import Dict, Any
from src.scan.detectors.utils import DetectionType
from src.scan.detectors.utils import (
    get_ruleset_dir,
    get_file_extension,
    create_temp_file
)


def run_semgrep(temp_file_path: str) -> Dict[str, Any]:
    try:
        ruleset_dir = get_ruleset_dir()
        result = subprocess.run(
            ['semgrep', '--config', ruleset_dir, '--metrics', 'off', '--json', temp_file_path],
            capture_output=True,
            check=True,
            text=True
        )        
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Semgrep failed: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Semgrep output: {str(e)}")


def process_finding(finding: Dict) -> DetectionType:
    try:
        detection: DetectionType = {
            "message": finding["extra"]["message"],
            "severity": finding["extra"]["severity"],
            "line_number": int(finding["start"]["line"])
        }
        return detection
    except KeyError as e:
        current_app.logger.error(
            f"Missing expected key in Semgrep result: {e}\n{finding}"
        )
        return {}


def detect_dynamic_execution_and_obfuscation(
    code_string: str,
    lang: str
) -> DetectionType:
    findings = [{}]
    extension = get_file_extension(lang)
    if extension:
        temp_file_path = create_temp_file(code_string, extension)
        if temp_file_path and os.path.exists(temp_file_path):
            findings = run_semgrep(temp_file_path)["results"]
            os.remove(temp_file_path)

    return process_finding(random.choice(findings))
