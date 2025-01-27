import pytest
from src.branch_protection import is_branch_included


# Mock for `get_branches_lists`
def mock_get_branches_lists(setting):
    data = {
        'BRANCHES_INCLUDE': {
            'repo1': ['main', 'dev'],
            'repo2': ['release']
        },
        'BRANCHES_EXCLUDE': {
            'repo1': ['test'],
            'repo3': ['staging']
        }
    }
    return data.get(setting, {})


# Patch the function for testing
@pytest.fixture(autouse=True)
def patch_get_branches_lists(monkeypatch):
    monkeypatch.setattr('src.branch_protection.get_branches_lists', mock_get_branches_lists)


@pytest.mark.parametrize("repo_name, branch_name, expected", [
    ('repo1', 'main', True),        # Included explicitly
    ('repo1', 'dev', True),         # Included explicitly
    ('repo1', 'test', False),       # Excluded explicitly
    ('repo2', 'release', True),     # Included explicitly
    ('repo2', 'main', False),       # Not included
    ('repo3', 'staging', False),    # Excluded explicitly
    ('repo3', 'main', False),       # Not included or excluded
])
def test_is_branch_included(repo_name, branch_name, expected):
    assert is_branch_included(repo_name, branch_name) == expected
