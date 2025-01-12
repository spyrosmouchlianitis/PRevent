from typing import List, Dict, Any
from flask import current_app, jsonify
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
from src.reviewers import resolve_reviewers
from src.scan.scan_logic import handle_scan
from src.secret_manager import get_secret
from src.settings import BLOCK_PR


class GitHubPRWebhook:
    def __init__(self):
        self.github_client = initialize_github_client()
        self.security_reviewers: List[str] = get_secret('SECURITY_REVIEWERS')
        self.protected_branches: Dict[str, List[str]] = get_secret('PROTECTED_BRANCHES')

    def on_pull_request(self, webhook_data: Dict[str, Any]) -> tuple:
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
                org_name,
                repo_name,
                branch_name,
                pr_number,
                commit_sha
            ) = extract_pr_info(webhook_data)

            # Should this branch be scanned?
            if not is_branch_included(repo_name, branch_name):
                return jsonify({
                    "message": f"{repo_name}:{branch_name} is not monitored, skipping"
                }), 204

            # Requires Repository permissions: Metadata -> Read
            repo = self.github_client.get_repo(repo_name)
            branch = repo.get_branch(branch_name)

            # Requires Repository Permissions: Pull requests -> Read
            pr = repo.get_pull(pr_number)

            # Malware-in-code scan
            status = handle_scan(repo, pr, commit_sha)

            # Trigger a code review (optional)
            self._trigger_code_review(status, pr, repo_name, org_name)

            # Block merging upon detection (optional)
            self._handle_block_mode(repo_name, branch_name)

            return jsonify({"message": "PR processed successfully"}), 200

        except KeyError as e:
            current_app.logger.error(f"Missing key in payload: {e}")
            return jsonify({"error": f"Missing key: {e}"}), 400
        except ValueError as e:
            current_app.logger.error(f"Invalid value encountered: {e}")
            return jsonify({"error": f"Invalid value: {e}"}), 400
        except GithubException as e:
            current_app.logger.error(f"GitHub API error: {e}")
            return jsonify({"error": "GitHub API request failed"}), 502

    def _trigger_code_review(
        self,
        status: str,
        pr: PullRequest,
        repo_name: str,
        org_name: str
    ) -> None:
        """
        If reviewers are defined, a review request is triggered upon detection.
        If block mode is enabled, merging is blocked until the scan passes.
        The scan passes either upon a code fix or upon a reviewer approval.
        """
        if status == 'failure':
            if self.security_reviewers:
                self._request_security_review(pr, repo_name, org_name)

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
        org_name: str
    ):
        try:
            security_reviewers = resolve_reviewers(
                self.security_reviewers,
                org_name,
                self.github_client
            ),

            # Requires Repository Permissions: Pull requests -> Read and write
            pr.create_review_request(reviewers=security_reviewers)
            current_app.logger.info(
                f"Requested review for {repo_name}, PR #{pr.number}"
            )

        except GithubException as e:
            current_app.logger.error(
                f"GitHub API error on review request for {repo_name}, PR #{pr.number}: {e}"
            )
            raise

    def on_pull_request_review(self, webhook_data: Dict[str, Any]) -> tuple:
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
            current_app.logger.info(
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

        return jsonify({"message": "PR review processed successfully"}), 200
