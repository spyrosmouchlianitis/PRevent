import re
from sys import getsizeof


def process_diff(diff: str, lang: str) -> list[tuple[int, str]]:
    """
    Receives a diff string and a language, cleans and verifies the diff,
    and returns a list of added lines with their line numbers.
    """
    diff = remove_comments(diff, lang)
    additions = get_additions_with_line_numbers(diff)  # Line numbers derived from hunk headers
    if not additions or getsizeof(diff) / (1024.0 ** 2) > 1:  # 1MB max diff size
        return []  # Return empty for non-applicable patches. Consider alerting on huge files.
    return additions


def get_additions_with_line_numbers(diff: str) -> list[tuple[int, str]]:
    """
    Extract added lines and their line numbers from a unified diff string.

    Args:
        diff (str): The unified diff string to process.

    Returns:
        list[tuple[int, str]]: A list of tuples, where each tuple contains:
            - The line number (int) of the added line.
            - The content (str) of the added line.

    Notes:
        - Lines starting with '+++' (file metadata) are ignored.
        - Lines starting with '+' represent added lines and are included,
          except those starting with '+++'.
        - The line numbers are adjusted based on the hunk headers (lines starting with '@@').
        - Non-deleted lines (not starting with '-') increment the line counter.
    """
    additions = []
    line_number = 0
    for line in diff.splitlines():
        if line.startswith('@@'):  # Extract the line number from the hunk header
            match = re.search(r'\+(\d+)', line)
            if match:
                line_number = int(match.group(1)) - 1  # Set starting line number
        # +: added lines, +++: metadata lines (not code)
        elif line.startswith('+') and not line.startswith('+++'):
            line_number += 1
            line_content = line[1:].strip()
            if line_content:
                additions.append((line_number, line_content))  # Remove '+' and add line
        elif not line.startswith('-'):  # Avoid counting non-deleted line
            line_number += 1
    return additions


def remove_comments(diff: str, lang: str):
    patterns = [
        {
            'languages': [
                'Bash',
                'Perl',
                'Python',
                'R',
                'Ruby',
                'Rust'
            ],
            'pattern': r'(?:^|\s)(#.*)',
        },
        {
            'languages': [
                'Dart',
                'Go',
                'Groovy',
                'JavaScript',
                'Kotlin',
                'Objective-C',
                'PHP',
                'Rust',
                'Scala',
                'Swift'
            ],
            'pattern': r'(?:^|\s)(//.*)',
        },
        {
            'languages': [
                'C',
                'C++',
                'CSS',
                'Dart',
                'Go',
                'Groovy',
                'JavaScript',
                'Kotlin',
                'Objective-C',
                'PHP',
                'Rust',
                'Scala',
                'Swift'
            ],
            'pattern': r'/\*[\s\S]*?\*/',
        },
        {
            'languages': ['Python'],
            'pattern': r'"""[\s\S]*?"""',
        },
        {
            'languages': ['Python'],
            'pattern': r"'''[\s\S]*?'''",
        },
        {
            'languages': ['Ruby'],
            'pattern': r'=begin[\s\S]*?=end',
        },
        {
            'languages': ['HTML'],
            'pattern': r'<!--[\s\S]*?-->',
        },
        {
            'languages': ['SQL'],
            'pattern': r'--.*',
        },
        {
            'languages': ['Lua'],
            'pattern': r'--\[\[[\s\S]*?\]\]',
        },
        {
            'languages': ['Clojure'],
            'pattern': r'(?:^|\s)(;.*)',
        }
    ]

    # Filter patterns by language (case-insensitive)
    matched_patterns = [
        p['pattern']
        for p in patterns
        if lang.lower() in list(map(lambda s: s.lower(), p['languages']))
    ]

    # Remove comments using the matched patterns
    for pattern in matched_patterns:
        diff = re.sub(pattern, '', diff, flags=re.MULTILINE)
    
    return diff
