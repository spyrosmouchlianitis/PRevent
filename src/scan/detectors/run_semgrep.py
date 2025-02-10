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
from src.settings import FP_STRICT, FULL_FINDINGS


def detect_dynamic_execution_and_obfuscation(
    code_string: str,
    extension: str
) -> list[DetectionType]:
    """
    Analyzes code for dynamic execution and obfuscation patterns using Semgrep.
    Save scanned code to a temporary file, remove it in the end.
    
    Return a list of findings regardless if full scan or first detection only.
    """
    findings = []
    temp_file_path: str = create_temp_file(code_string, extension)
    if temp_file_path and os.path.exists(temp_file_path):
        findings: list = run_semgrep(temp_file_path)
        os.remove(temp_file_path)
    if findings and not FULL_FINDINGS:
        while (result := random.choice(findings)) is None:
            pass
        return [process_semgrep_finding(result)] if result else []
    return [result for f in findings if (result := process_semgrep_finding(f)) is not None]


def run_semgrep(temp_file_path: str) -> list[dict[str, Any]]:
    try:
        ruleset_dir = get_ruleset_dir()
        command = [
            'semgrep',
            '--config', ruleset_dir,
            '--metrics', 'off',
            '--max-target-bytes', '2000000',
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

        results = []
        # Prioritize performance
        if FULL_FINDINGS:  # Collect all results
            for line in process.stdout:
                if line.strip():
                    parsed_output = json.loads(line)
                    results.extend(parsed_output["results"])
        else:  # Stop after the first result
            for line in process.stdout:
                if line.strip():
                    parsed_output = json.loads(line)
                    results.extend(parsed_output["results"])
                    process.terminate()
                    break

        process.wait()  # Clean termination
        return results

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
