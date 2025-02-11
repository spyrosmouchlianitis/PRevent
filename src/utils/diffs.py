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


# Languages listed as they appear in src/scan/languages.py values
def remove_comments(diff: str, lang: str) -> str:
    # First preserve strings to avoid matching inside them
    diff, strings = preserve_strings(diff)
    
    # Get and apply comment patterns for the language
    patterns = get_comment_patterns(lang)
    diff = remove_comment_patterns(diff, patterns)
    
    # Restore the preserved strings
    diff = restore_strings(diff, strings)
    
    return diff


def preserve_strings(diff: str) -> tuple[str, list[str]]:
    """
    Temporarily remove strings to allow clean comments removal. Restore after removal.
    Each string gets unique numbered placeholder that ensures correct restoration order.
    """
    strings = []
    
    # Single pattern to match any quote-delimited string, properly handling escapes
    def replace_string(match):
        strings.append(match.group(0))
        return f'__STRING_{len(strings)-1}__'
    
    try:
        processed_diff = re.sub(r'(?<![\'"])([\'"])(?!\1\1)(?:\\.|[^\\\n])*?(?<!\\)\1', replace_string, diff)
    except Exception:
        # If pattern fails, return original diff
        return diff, []
    
    return processed_diff, strings


def remove_comment_patterns(diff: str, patterns: list[str]) -> str:
    """Remove all comment patterns from the diff."""
    result = diff
    for pattern in patterns:
        try:
            result = re.sub(r'[\s\t]*' + pattern, '', result, flags=re.MULTILINE)
        except Exception:
            continue
    return result


def get_comment_patterns(lang: str) -> list[str]:
    """Get list of comment patterns that apply to the given language."""
    patterns = [
        {
            'languages': ['Bash', 'Perl', 'Python', 'R', 'Ruby', 'Rust'],
            'pattern': r'#.*$',
        },
        {
            'languages': [
                'Dart', 'dotnet', 'Go', 'Groovy', 'Java', 'JavaScript',
                'Kotlin', 'Objective-C', 'PHP', 'Rust', 'Scala', 'Swift'
            ],
            'pattern': r'//.*$',
        },
        {
            'languages': [
                'C', 'C++', 'CSS', 'dotnet', 'Dart', 'Go', 'Groovy',
                'Java', 'JavaScript', 'Kotlin', 'Objective-C', 'PHP',
                'Rust', 'Scala', 'Swift'
            ],
            'pattern': r'/\*[\s\S]*?\*/',
        },
        {
            'languages': ['Clojure'],
            'pattern': r';.*$',
        },
        {
            'languages': ['HTML', 'dotnet'],
            'pattern': r'<!--[\s\S]*?-->',
        },
        {
            'languages': ['Lua'],
            'pattern': r'--[\s\S].*$',
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
            'languages': ['SQL'],
            'pattern': r'--.*',
        }
    ]
    
    return [
        p['pattern']
        for p in patterns
        if lang.lower() in map(str.lower, p['languages'])
    ]


def restore_strings(diff: str, strings: list[str]) -> str:
    """Restore strings in the diff from numbered placeholders."""
    for i, string in enumerate(strings):
        diff = diff.replace(f'__STRING_{i}__', string)
    return diff
