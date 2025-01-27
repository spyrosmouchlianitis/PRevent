import pytest
from unittest.mock import patch
from src.utils.patch import remove_comments, process_diff, get_additions_with_line_numbers

lang = "python"


def test_process_diff_with_additions():
    diff = "some diff content"
    expected_additions = [(1, "added line")]
    
    with patch('src.scan.patch_utils.remove_comments', return_value=diff) as mock_remove_comments, \
         patch('src.scan.patch_utils.get_additions_with_line_numbers', return_value=expected_additions) \
         as mock_get_additions:
        result = process_diff(diff, lang)
        assert result == expected_additions
        mock_remove_comments.assert_called_once_with(diff, lang)
        mock_get_additions.assert_called_once_with(diff)


def test_process_diff_with_no_additions():
    diff = "some diff content"
    expected_additions = []
    
    with patch('src.scan.patch_utils.remove_comments', return_value=diff) as mock_remove_comments, \
         patch('src.scan.patch_utils.get_additions_with_line_numbers', return_value=expected_additions) \
         as mock_get_additions:
        result = process_diff(diff, lang)
        assert result == expected_additions
        mock_remove_comments.assert_called_once_with(diff, lang)
        mock_get_additions.assert_called_once_with(diff)


@pytest.mark.parametrize(
    "lang, diff, expected_result",
    [
        ("Python", "print('Hello World')\n# This is a comment", "print('Hello World')\n"),
        ("Python", "print('Hello World')\n'''multi-line\ncomment'''", "print('Hello World')\n"),
        ("Ruby", "puts 'Hello'\n=begin\ncomment block\n=end", "puts 'Hello'\n"),
        ("HTML", "<div>content</div><!-- comment -->", "<div>content</div>"),
        ("SQL", "SELECT * FROM table -- comment", "SELECT * FROM table "),
        ("C", "int main() { /* comment */ }", "int main() {  }"),
        ("JavaScript", "let x = 5; // inline comment", "let x = 5; "),
        ("Go", "func main() { } // comment", "func main() { } "),
        ("Lua", "print('hello') --[[ comment ]]", "print('hello') "),
        ("Clojure", "(defn foo []) ; comment", "(defn foo []) ")
    ]
)
def test_remove_comments(_lang, diff, expected_result):
    result = remove_comments(diff, _lang)
    assert result.strip() == expected_result.strip()


def test_get_additions_with_line_numbers():
    # Test input with no additions
    diff = '--- a/file\n+++ b/file\n@@ -1,3 +1,3 @@\n-removed line\nunchanged line\n'
    assert get_additions_with_line_numbers(diff) == []

    # Test input with single addition
    diff = '--- a/file\n+++ b/file\n@@ -1,3 +1,4 @@\n-removed line\nunchanged line\n+added line 1\n'
    assert get_additions_with_line_numbers(diff) == [(2, "added line 1")]

    # Test input with multiple additions
    diff = '--- a/file\n+++ b/file\n@@ -1,3 +1,5 @@\n-removed line\nunchanged line\n+added line 1\n+added line 2\n'
    assert get_additions_with_line_numbers(diff) == [(2, 'added line 1'), (3, 'added line 2')]

    # Test input with addition and metadata line
    diff = '--- a/file\n+++ b/file\n@@ -1,3 +1,4 @@\n-removed line\nunchanged line\n+++ added metadata\n+added line 1\n'
    assert get_additions_with_line_numbers(diff) == [(3, "added line 1")]

    # Test input with multiple hunks
    diff = '--- a/file\n+++ b/file\n@@ -1,3 +1,4 @@\n-removed line\nunchanged line\n+added line 1\n@@ -5,3 +6,3 @@\n-removed line\nunchanged line\n+added line 2\n'
    assert get_additions_with_line_numbers(diff) == [(2, "added line 1"), (7, "added line 2")]

    # Test input with trailing empty lines
    diff = '--- a/file\n+++ b/file\n@@ -1,3 +1,4 @@\n-removed line\nunchanged line\n+added line 1\n'
    assert get_additions_with_line_numbers(diff) == [(2, "added line 1")]
