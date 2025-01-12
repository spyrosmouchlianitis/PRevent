from github import Github
from github.GithubException import GithubException
from flask import current_app


def resolve_reviewers(
    security_reviewers: list[str],
    org_name: str,
    github_client: Github
) -> list[str]:
    reviewers = []
    for reviewer in security_reviewers:
        if reviewer.startswith("team:"):
            team_id = int(reviewer.replace("team:", ""))
            team_members = fetch_team_members(org_name, team_id, github_client)
            reviewers.extend(team_members)
        else:  # If it's a user ID
            reviewers.append(reviewer)
    return reviewers


def fetch_team_members(
    org_name: str,
    team_id: int,
    github_client: Github
) -> list[str]:
    try:
        # Require Organization Permissions: Members -> Read
        team = github_client.get_organization(org_name).get_team(team_id)
        members = team.get_members()

        return [member.login for member in members]
    except GithubException as e:
        current_app.logger.error(
            f"GitHub API error fetching team members for team {team_id}: {e}"
        )
        return []
