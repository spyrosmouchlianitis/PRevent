import hmac
import hashlib
import time
from datetime import datetime
from flask import current_app, request
from werkzeug.exceptions import Unauthorized
from github import Github
from typing import Dict, Any
from src.secret_manager import get_secret


def extract_pr_info(webhook_data: Dict[str, Any]) -> tuple:
    try:
        org_name = webhook_data['repository']['owner']['login']
        repo_name = webhook_data['repository']['full_name']
        branch_name = webhook_data['pull_request']['base']['ref']
        pr_number = webhook_data['pull_request']['number']
        commit_sha = webhook_data['pull_request']['head']['sha']
        action = webhook_data['action']
        return org_name, repo_name, branch_name, pr_number, commit_sha, action
    except KeyError as e:
        current_app.logger.error(f"Missing expected key: {e}")


def extract_review_info(webhook_data: Dict[str, Any]) -> tuple:
    try:
        repo_name = webhook_data['repository']['full_name']
        branch_name = webhook_data['pull_request']['head']['ref']
        pr_number = webhook_data['pull_request']['number']
        review_state = webhook_data['review']['state']
        reviewer = webhook_data['review']['user']['login']
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
