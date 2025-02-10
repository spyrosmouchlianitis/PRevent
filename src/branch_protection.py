import requests
from fastapi.logger import logger
from src.secret_manager import get_secret, set_secret
from src.github_client import token_headers
from src.settings import SCAN_CONTEXT


def is_branch_included(repo_name, branch_name) -> bool:
    """
    Checks if a branch is included in the protected branches list, based on defined
    inclusion and exclusion lists. By default, all branches across all repositories are included,
    until overridden by the `BRANCHES_INCLUDE` or `BRANCHES_EXCLUDE` settings.

    Args:
        repo_name (str): Repository name.
        branch_name (str): Branch name.

    Returns:
        bool: True if the branch is included, False if excluded or not explicitly included.
    """
    include_branches = get_secret('BRANCHES_INCLUDE')
    exclude_branches = get_secret('BRANCHES_EXCLUDE')

    if repo_name in exclude_branches:
        if exclude_branches[repo_name] == 'all' or branch_name in exclude_branches[repo_name]:
            return False
    
    if include_branches:
        if repo_name not in include_branches:
            return False
        elif include_branches[repo_name] == 'all':
            return True
        elif branch_name not in include_branches[repo_name]:
            return False

    return True


def get_existing_protection_conf(repo_name: str, branch_name: str) -> dict:
    """
    Fetches the full branch protection rule for a given branch.
    In GitHub, all sub-rules are organized together in a single parent rule.
    When modifying this app's protection settings, handle the rest.

    Returns:
        dict: The protection settings of the branch.
    """

    # Use `requests` because GitHub's API has discrepancies here that PyGithub doesn't handle.
    url = f"https://api.github.com/repos/{repo_name}/branches/{branch_name}"
    response = requests.get(url, headers=token_headers())
    return response.json().get("protection", {})


def apply_branch_protection_rule(
    repo_name: str,
    branch_name: str,
    protection: dict
) -> None:
    """
    Apply protection by this app's check to the specified branch, preserving existing protections.

    Args:
        - "required_status_checks" (required): Contains `strict` and `checks`.
            - "strict" (required): Requires all past checks to pass.
            - "checks" (required): list of checks that must pass.
                - "contexts" (required): Check identifiers. Used when `app_id` is not provided.
                - "app_id" (optional): Associates a context with a specific GitHub app.
        - "enforce_admins" (required): Enforced globally. Set to `True` unless other checks exist.
        - "required_pull_request_reviews" (required): Unmodified.
        - "restrictions" (required): Unmodified.

    Merge new settings with existing ones, without altering other protection rules.
    Handle both old and new schema versions.

    Requires:
        - Repository Permissions: Branches -> Write

    For more info:
        https://docs.github.com/en/rest/branches/branch-protection?apiVersion=2022-11-28
    """

    # If "strict" is already set to "True" for existing protection rules,
    # it will require all previous commits to be scanned by this app, which is currently unsupported.
    # Therefore, in such case, the new protection rule is not enforced.
    strict_top_level = protection.get("strict", False)
    strict_nested = protection.get("required_status_checks", {}).get("strict", False)
    strict = strict_top_level or strict_nested
    contexts = protection.get("contexts", [])
    checks = protection.get("required_status_checks", {}).get("checks", [])
    if strict:
        if contexts or checks:
            logger.error(
                "strict=True is applied on existing rules, not adding new protection to avoid deadlock.\n"
                f"Did not enforce branch protection on {repo_name}/{branch_name}"
            )
            return None

    # Merge only the fields that should be modified or added
    data = {
        "required_status_checks": {
            "strict": strict,
            "checks": checks
        },
        "enforce_admins": protection.get("enforce_admins", True),
        "required_pull_request_reviews": protection.get("required_pull_request_reviews", None),
        "restrictions": protection.get("restrictions", None)
    }

    # Migrate "contexts" from old API to new schema
    for context in contexts:
        data["required_status_checks"]["checks"].append({"context": context})

    # Add new app-specific check
    data["required_status_checks"]["checks"].append({
        "context": SCAN_CONTEXT,
        "app_id": int(get_secret('GITHUB_APP_INTEGRATION_ID'))
    })

    # Use `requests` because PyGithub supports only the old version of this call.
    url = f"https://api.github.com/repos/{repo_name}/branches/{branch_name}/protection"
    response = requests.put(url, json=data, headers=token_headers())
    if response.status_code != 200:
        logger.error(
            "Failed to update branch protection", 
            extra={
                "status_code": response.status_code,
                "response": response.json(),
                "repo": repo_name,
                "branch": branch_name
            }
        )


def is_branch_status_check_protected(protection: dict) -> bool:
    """
    Checks if a branch has a protection rule defined by this app.
    """
    checks = protection.get("required_status_checks", {}).get("checks", [])
    return any(check.get("context") == SCAN_CONTEXT for check in checks)


def update_protected_branches(
    protected_branches: dict[str, list[str]],
    repo_name: str,
    branch_name: str
) -> dict[str, list[str]]:
    """
    Update the list of protected branches for a given repository.
    This allows tracking branches, avoiding setting a protection rule over and over.
    Update both state and secret.

    Args:
        protected_branches (dict[str, list[str]]):
            Current protected branches (values) by repository (key).
        repo_name: ...
        branch_name: ...

    Returns:
        dict[str, list[str]]: Updated mapping of protected repositories and branches.

    Side Effects:
        Updates the 'PROTECTED_BRANCHES' secret with the new protected branch list.
    """

    protected_branches.setdefault(repo_name, [])
    if branch_name not in protected_branches[repo_name]:
        protected_branches[repo_name].append(branch_name)
        set_secret('PROTECTED_BRANCHES', protected_branches)
    return protected_branches
