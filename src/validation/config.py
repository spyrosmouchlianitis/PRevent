from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import Any, Union
from src.secret_manager import get_secret
from src.settings import SECRET_MANAGER, BLOCK_PR, FP_STRICT, WEBHOOK_PORT, JWT_EXPIRY_SECONDS


def validate_config_parameters() -> None:
    
    validate_secret_manager(SECRET_MANAGER)
    validate_block_pr(BLOCK_PR)
    validate_fp_strict(FP_STRICT)
    validate_webhook_port(WEBHOOK_PORT)
    validate_jwt_expiry_seconds(JWT_EXPIRY_SECONDS)
    
    validate_github_app_integration_id(get_secret('GITHUB_APP_INTEGRATION_ID'))
    validate_github_app_private_key(get_secret('GITHUB_APP_PRIVATE_KEY'))
    validate_webhook_secret(get_secret('WEBHOOK_SECRET'))
    validate_branches(get_secret('BRANCHES_INCLUDE'))
    validate_branches(get_secret('BRANCHES_EXCLUDE'))
    validate_security_reviewers(get_secret('SECURITY_REVIEWERS'))
    
    return True


def validate_secret_manager(value: str) -> None:
    allowed_values = ["vault", "aws", "azure", "gcloud", "local"]
    if value not in allowed_values:
        raise ValueError(f"SECRET_MANAGER must be one of: {', '.join(allowed_values)}")


def validate_github_app_private_key(value: str) -> None:
    try:
        serialization.load_pem_private_key(
            value.encode(),
            password=None,
            backend=default_backend() 
        ) 
    except Exception as e: 
        raise ValueError(f"Invalid GITHUB_APP_PRIVATE_KEY: {e}")


def validate_github_app_integration_id(value: Union[str, int]) -> None:
    if not isinstance(value, str) or not value.isdigit() or not 5 <= len(value) <= 12:
        raise ValueError("GITHUB_APP_INTEGRATION_ID must be a string of digits of 5-12 length")


def validate_webhook_secret(value: str) -> None:
    if not isinstance(value, str) or len(value) < 32:
        raise ValueError("WEBHOOK_SECRET must be a string with at least 32 characters")


def validate_branches(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("BRANCHES_INCLUDE/EXCLUDE must be a dictionary")
    for k, v in value.items():
        if not isinstance(k, str):
            raise ValueError("Repositories (branch keys) must be strings")
        if not isinstance(v, (list, str)):
            raise ValueError("Branch values must be lists or strings")


def validate_security_reviewers(value: Any) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("SECURITY_REVIEWERS must be a list of strings")


def validate_block_pr(value: Any) -> None:
    if not isinstance(value, bool):
        raise ValueError("BLOCK_PR must be a boolean")


def validate_fp_strict(value: Any) -> None:
    if not isinstance(value, bool):
        raise ValueError("FP_STRICT must be a boolean")


def validate_webhook_port(value: Any) -> None:
    if not isinstance(value, int) or not 1024 <= value <= 65535:
        raise ValueError("WEBHOOK_PORT must be an integer between 1024 and 65535")


def validate_jwt_expiry_seconds(value: Any) -> None:
    if not isinstance(value, int) or value < 10:
        raise ValueError("JWT_EXPIRY_SECONDS must be a positive integer above 10")
