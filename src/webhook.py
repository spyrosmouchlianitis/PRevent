from typing import Any
from fastapi.responses import JSONResponse
from fastapi.logger import logger
from github import PullRequest
from github.GithubException import GithubException
from src.github_client import initialize_github_client
from src.utils.github import create_commit_status
from src.utils.webhook import (
    extract_pr_info,
    extract_review_info
)
from src.branch_protection import (
    is_branch_included,
    is_branch_status_check_protected,
    get_existing_protection_conf,
    apply_branch_protection_rule,
    update_protected_branches
)
from src.scan.scan_logic import process_scan
from src.secret_manager import get_secret
from src.settings import BLOCK_PR


class GitHubPRWebhook:
    def __init__(self):
        self.github_client = initialize_github_client()
        self.security_reviewers: list[str] = get_secret('SECURITY_REVIEWERS')
        self.protected_branches: dict[str, list[str]] = get_secret('PROTECTED_BRANCHES')

    def on_pull_request(self, webhook_data: dict[str, Any]) -> tuple:
        """
        Process a pull request event:
        1. Check if the branch is protected.
        2. Perform a security scan on the pull request.
        3. Update the commit status based on the scan results.
        4. Request a security review if the scan failed (optional).
        5. Block merging until a reviewer's approval is received (optional).
        """

        try:
            (
                repo_name,
                branch_name,
                pr_number,
                commit_sha
            ) = extract_pr_info(webhook_data)

            # Should this branch be scanned?
            if not is_branch_included(repo_name, branch_name):
                return JSONResponse(
                    content={"message": f"{repo_name}:{branch_name} is not monitored, skipping"},
                    status_code=204
                )

            # Requires Repository permissions: Metadata -> Read
            repo = self.github_client.get_repo(repo_name)

            # Requires Repository Permissions: Pull requests -> Read
            pr = repo.get_pull(pr_number)

            # Malicious-code scan
            status = process_scan(repo, pr, commit_sha)

            # Trigger a code review (optional)
            self._request_code_review(status, pr, repo_name)

            # Block merging upon detection (optional)
            self._handle_block_mode(repo_name, branch_name)

            return JSONResponse(content={"message": "PR processed successfully"}, status_code=200)

        except KeyError as e:
            logger.error(f"Missing key in payload: {e}")
            return JSONResponse(content={"error": f"Missing key: {e}"}, status_code=400)
        except ValueError as e:
            logger.error(f"Invalid value encountered: {e}")
            return JSONResponse(content={"error": f"Invalid value: {e}"}, status_code=400)
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            return JSONResponse(content={"error": "GitHub API request failed"}, status_code=502)

    def _request_code_review(
        self,
        status: str,
        pr: PullRequest,
        repo_name: str
    ) -> None:
        """
        If reviewers are defined, a review request is triggered upon detection.
        If block mode is enabled, merging is blocked until the scan passes.
        The scan passes either upon a code fix or upon a reviewer approval.
        """
        if status == 'failure':
            if self.security_reviewers:
                self._request_security_review(pr, repo_name)

    def _handle_block_mode(self, repo_name, branch_name):
        """
        1. Apply branch protection upon the first monitored pull request of a protected branch.
        2. Track protected branches.
        """

        if self.security_reviewers and BLOCK_PR:
            """
            An initial "success" status could prevent unintentional blocking due to errors,
            but it creates a brief window for merging infected code, so we avoid it.

            You can change it, by adding the following call bellow this comment,
            and at the beginning of `on_pull_request`:
            
            create_commit_status(repo, pr.head.sha, "success", "Pass by default (set by user)")
            """

            protection = get_existing_protection_conf(repo_name, branch_name)
            if not is_branch_status_check_protected(protection):
                apply_branch_protection_rule(repo_name, branch_name, protection)
                self.protected_branches = update_protected_branches(
                    self.protected_branches,
                    repo_name,
                    branch_name
                )

    def _request_security_review(
        self,
        pr: PullRequest,
        repo_name: str,
    ):
        # Separate requests so if one request fails the rest still succeed.
        team_reviewers = []
        individual_reviewers = []
        for reviewer in self.security_reviewers:
            if reviewer.startswith("team:"):
                team_reviewers.append(reviewer[5:])
            else:
                individual_reviewers.append(reviewer)
        try:
            pr.create_review_request(team_reviewers=team_reviewers, reviewers=individual_reviewers)
            logger.info(
                f"Requested review from {self.security_reviewers} for {repo_name}, PR #{pr.number}"
            )
        except GithubException as e:
            logger.error(
                f"GitHub API error on review request for {repo_name}, PR #{pr.number}: {e}"
            )

    def on_pull_request_review(self, webhook_data: dict[str, Any]) -> tuple:
        """
        Change check status to "success" upon a pull request review approval event.
        If blocking mode (branch protection) was applied, this will release the block.
        """
        (
            repo_name,
            branch_name,
            pr_number,
            review_state,
            reviewer
        ) = extract_review_info(webhook_data)

        if review_state.lower() == "approved":
            logger.info(
                f"Review approved by {reviewer}: {repo_name}/{branch_name}, PR #{str(pr_number)}"
            )
            if reviewer in self.security_reviewers:
                repo = self.github_client.get_repo(repo_name)
                pr = repo.get_pull(pr_number)
                create_commit_status(
                    repo,
                    pr.head.sha,
                    "success",
                    f"Approved by {reviewer}"
                )

        return JSONResponse(content={"message": "PR review processed successfully"}, status_code=200)
