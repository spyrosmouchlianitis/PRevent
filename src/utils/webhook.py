import re
import hmac
import hashlib
import time
from datetime import datetime
from flask import current_app, request
from werkzeug.exceptions import Unauthorized
from github import Github
from typing import Dict, Any
from src.secret_manager import get_secret


def validate_string(string: str) -> None:
    if not re.fullmatch(r'^[\w$/_\-\[\].]{1,50}$', string):
        raise ValueError(f"Invalid parameter value: {string}")


def validate_pr_number(number: int) -> None:
    try:
        int(number)
        if number > 100000:
            raise ValueError("PR number must be smaller than 100,000.")
    except ValueError:
        raise ValueError(f"Invalid PR number value: {number}")


def validate_sha(sha: str) -> str:
    if not re.match(r'^[a-fA-F0-9]{40}$', sha):
        raise ValueError(f"Invalid parameter value: {sha}")


def extract_pr_info(webhook_data: Dict[str, Any]) -> tuple:
    try:
        org_name = webhook_data['repository']['owner']['login']
        repo_name = webhook_data['repository']['full_name']
        branch_name = webhook_data['pull_request']['base']['ref']
        pr_number = webhook_data['pull_request']['number']
        commit_sha = webhook_data['pull_request']['head']['sha']

        validate_string(org_name)
        validate_string(repo_name)
        validate_string(branch_name)
        validate_pr_number(pr_number)
        validate_sha(commit_sha)

        return org_name, repo_name, branch_name, pr_number, commit_sha

    except KeyError as e:
        current_app.logger.error(f"Missing expected key: {e}")
        raise ValueError(f"Missing expected key: {e}")


def validate_review_state(state: str) -> None:
    valid_states = {'approved', 'changes_requested', 'commented', 'dismissed', 'pending'}
    if state.lower() not in valid_states:
        raise ValueError(f"Invalid review state: {state}")


def extract_review_info(webhook_data: Dict[str, Any]) -> tuple:
    try:
        repo_name = webhook_data['repository']['full_name']
        branch_name = webhook_data['pull_request']['head']['ref']
        pr_number = webhook_data['pull_request']['number']
        review_state = webhook_data['review']['state']
        reviewer = webhook_data['review']['user']['login']

        validate_string(repo_name)
        validate_string(branch_name)
        validate_pr_number(pr_number)
        validate_review_state(review_state)
        validate_string(reviewer)

        return repo_name, branch_name, pr_number, review_state, reviewer

    except KeyError as e:
        current_app.logger.error(f"Missing expected key: {e}")
        raise ValueError("Invalid webhook_data format")


def verify_webhook_signature(event_request: request) -> None:
    signature_header: str = event_request.headers.get('X-Hub-Signature-256', '')
    if not signature_header:
        current_app.logger.error("Missing X-Hub-Signature header.")
        raise Unauthorized("Missing X-Hub-Signature header")

    secret_token = get_secret('WEBHOOK_SECRET')
    payload_body: bytes = event_request.get_data()
    computed_signature = 'sha256=' + hmac.new(
        secret_token.encode("utf-8"),  # Ensure it's bytes
        payload_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, signature_header):
        current_app.logger.error("Invalid webhook signature.")
        raise Unauthorized("Invalid webhook signature")


def check_rate_limit(github_client: Github) -> None:
    rate_limit = github_client.get_rate_limit().core
    remaining = rate_limit.remaining
    reset_time = rate_limit.reset  # (Unix timestamp)

    if remaining < 5:
        time_delta = reset_time.replace(tzinfo=None) - datetime.now()
        sleep_seconds = time_delta.total_seconds()
        if sleep_seconds > 0:
            current_app.logger.warning(
                f"Approaching rate limit. Sleeping for {sleep_seconds} seconds."
            )
            time.sleep(sleep_seconds)

    return None
