import os
import requests
import subprocess


def is_vault_configured() -> bool:
    vault_url = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    vault_token_path = os.path.expanduser("~/.vault-token")

    if not os.path.exists(vault_token_path):
        return False

    with open(vault_token_path, "r") as token_file:
        vault_token = token_file.read().strip()

    response = requests.get(
        f"{vault_url}/v1/sys/health", 
        headers={"X-Vault-Token": vault_token}
    )
    return response.status_code == 200


def is_aws_configured() -> bool:
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity"], check=False, capture_output=True
    )
    return result.returncode == 0


def is_azure_configured() -> bool:
    result = subprocess.run(
        ["az", "keyvault", "list"], check=False, capture_output=True
    )
    return result.returncode == 0


def is_gcloud_configured() -> bool:
    result = subprocess.run(
        ["gcloud", "auth", "list"], check=False, capture_output=True
    )
    return result.returncode == 0


def is_local_configured() -> bool:
    return is_vault_configured()


def is_sm_configured(manager: str) -> bool:
    config_methods = {
        'vault': is_vault_configured,
        'aws': is_aws_configured,
        'azure': is_azure_configured,
        'gcloud': is_gcloud_configured,
        'local': is_local_configured,
    }
    if manager in config_methods:
        return config_methods[manager]()
    else:
        return False
