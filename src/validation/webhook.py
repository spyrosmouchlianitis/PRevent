import re


def validate_string(string: str) -> None:
    pattern = re.compile(r'^[\w$/_\-\[\].]{1,50}$')
    if not pattern.fullmatch(string):
        raise ValueError(f"Invalid parameter value: {string}")


def validate_pr_number(number: int) -> None:
    try:
        int(number)
        if number > 100000:
            raise ValueError("PR number must be smaller than 100,000.")
    except ValueError:
        raise ValueError(f"Invalid PR number value: {number}")


def validate_sha(sha: str) -> None:
    pattern = re.compile(r'^[a-fA-F0-9]{40}$')
    if not pattern.fullmatch(sha):
        raise ValueError(f"Invalid parameter value: {sha}")
