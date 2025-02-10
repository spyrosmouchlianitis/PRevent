import hmac
import hashlib
import time
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.logger import logger
from github import Github
from typing import Any
from src.validation.webhook import validate_string, validate_pr_number, validate_sha
from src.secret_manager import get_secret


def extract_pr_info(webhook_data: dict[str, Any]) -> tuple:
    try:
        repo_name = webhook_data['repository']['full_name']
        branch_name = webhook_data['pull_request']['base']['ref']
        pr_number = webhook_data['pull_request']['number']
        commit_sha = webhook_data['pull_request']['head']['sha']

        validate_string(repo_name)
        validate_string(branch_name)
        validate_pr_number(pr_number)
        validate_sha(commit_sha)

        return repo_name, branch_name, pr_number, commit_sha

    except KeyError as e:
        logger.error(f"Missing expected key: {e}")
        raise ValueError(f"Missing expected key: {e}")


def validate_review_state(state: str) -> None:
    valid_states = {'approved', 'changes_requested', 'commented', 'dismissed', 'pending'}
    if state.lower() not in valid_states:
        raise ValueError(f"Invalid review state: {state}")


def extract_review_info(webhook_data: dict[str, Any]) -> tuple:
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
        logger.error(f"Missing expected key: {e}")
        raise ValueError("Invalid webhook_data format")

async def verify_webhook_signature(event_request: Request) -> None:
    signature_header: str = event_request.headers.get('X-Hub-Signature-256', '')
    if not signature_header:
        logger.error("Missing X-Hub-Signature header.")
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature header")

    secret_token = get_secret('WEBHOOK_SECRET')
    payload_body: bytes = await event_request.body()
    computed_signature = 'sha256=' + hmac.new(
        secret_token.encode("utf-8"),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, signature_header):
        logger.error("Invalid webhook signature.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


def check_rate_limit(github_client: Github) -> None:
    rate_limit = github_client.get_rate_limit().core
    remaining = rate_limit.remaining
    reset_time = rate_limit.reset  # (Unix timestamp)

    if remaining < 5:
        time_delta = reset_time.replace(tzinfo=None) - datetime.now()
        sleep_seconds = time_delta.total_seconds()
        if sleep_seconds > 0:
            logger.warning(
                f"Approaching rate limit. Sleeping for {sleep_seconds} seconds."
            )
            time.sleep(sleep_seconds)

    return None
