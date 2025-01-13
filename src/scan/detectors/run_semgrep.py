import os
import json
import tempfile
import subprocess
from flask import current_app
from typing import Tuple, List, Dict, Any
from src.scan.languages import major
from src.settings import RULESET_REPO, RULESET_DIR


def handle_ruleset():
    if not os.path.exists(RULESET_DIR):
        subprocess.run(['git', 'clone', RULESET_REPO, RULESET_DIR], check=True)
    else:
        # Fetch latest changes
        subprocess.run(['git', 'fetch', 'origin'], cwd=RULESET_DIR, check=True)
        # Quickly check if local is behind
        result = subprocess.run(['git', 'rev-list', '--count', 'HEAD..origin/main'], cwd=RULESET_DIR, capture_output=True, text=True)
        if int(result.stdout.strip()) > 0:
            subprocess.run(['git', 'pull', 'origin', 'main'], cwd=RULESET_DIR, check=True)


def get_file_extension(lang: str) -> str:
    return next((key for key, val in major.items() if val == lang))


def create_temp_file(code_string: str, extension: str) -> str:
    with tempfile.NamedTemporaryFile(
        delete=False, mode='w', suffix=f'.{extension}'
    ) as temp_file:
        temp_file.write(code_string)
        return temp_file.name


def run_semgrep(temp_file_path: str) -> Dict[str, Any]:
    handle_ruleset()

    result = subprocess.run(
        ['semgrep', '--config', RULESET_DIR, '--json', temp_file_path],
        capture_output=True,
        check=True,
        text=True
    )
    
    return json.loads(result.stdout)


def process_findings(
    findings: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    obfuscation = []
    dynamic_execution = []

    for finding in findings:
        try:
            detection = {
                "detection": finding["extra"]["message"],
                "severity": finding["extra"]["severity"],
                "line_number": int(finding["start"]["line"])
            }
            check_type = finding["check_id"].split('ruleset.')[1].split('.')[0]
            if check_type == 'obfuscation':
                obfuscation.append(detection)
            elif check_type == 'dynamic_execution':
                dynamic_execution.append(detection)
        except KeyError as e:
            current_app.logger.error(
                f"Missing expected key in Semgrep result: {e}\n{finding}"
            )
        except IndexError as e:
            current_app.logger.error(
                f"Failed to parse check_id in Semgrep result: {e}\n{finding}"
            )

    return obfuscation, dynamic_execution


def detect_dynamic_execution_and_obfuscation(
    code_string: str,
    lang: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    temp_file_path = None  # Ensure it's defined
    try:
        extension = get_file_extension(lang)
        temp_file_path = create_temp_file(code_string, extension)
        findings = run_semgrep(temp_file_path)["results"]
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Semgrep failed. Code: {e.returncode}, Message: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Semgrep output: {str(e)}")
    finally:
        # Clean up: delete the temporary file if it was created
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return process_findings(findings)
