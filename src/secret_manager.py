import os
import json
import importlib
from src import settings
from fastapi.logger import logger
from typing import Any


def log_and_raise_value_error(message: str):
    logger.error(message)
    raise ValueError(message)


def get_secret(key: str) -> Any:
    secret_getters = {
        "aws": aws_get_secret,
        "azure": azure_get_secret,
        "gcloud": gcloud_get_secret,
        "vault": vault_get_secret,
        "local": vault_get_secret,
    }
    secret_manager = getattr(settings, "SECRET_MANAGER", None)
    if not secret_manager:
        log_and_raise_value_error(
            "'SECRET_MANAGER' isn't set in src/settings.py. Set it, or run setup.py."
        )
        print("\nOptions: 'aws', 'azure', 'gcloud', 'vault', 'local'")
    if secret_manager not in secret_getters:
        raise NotImplementedError(
            f"get_secret not implemented for '{secret_manager}'"
        )
    secret = secret_getters[secret_manager](key)
    return json.loads(secret)


def set_secret(key: str, value: Any) -> None:
    secret_setters = {
        "aws": aws_set_secret,
        "azure": azure_set_secret,
        "gcloud": gcloud_set_secret,
        "vault": vault_set_secret,
        "local": vault_set_secret,
    }
    secret_manager = getattr(settings, "SECRET_MANAGER", None)
    if not secret_manager:
        log_and_raise_value_error("'SECRET_MANAGER' is not set in src/settings.py.")
        print("Options: 'aws', 'azure', 'gcloud', 'vault', 'local'")
    if secret_manager not in secret_setters:
        raise NotImplementedError(
            f"set_secret not implemented for '{secret_manager}'"
        )
    secret_setters[secret_manager](key, json.dumps(value))


# AWS Secrets Manager

def init_aws_client(region_name: str):
    boto3 = importlib.import_module("boto3")
    return boto3.client('secretsmanager', region_name=region_name)


def aws_get_secret(key: str) -> str:
    region_name = getattr(settings, "AWS_REGION", "us-east-1")
    client = init_aws_client(region_name)
    response = client.get_secret_value(SecretId=key)
    return response['SecretString']


def aws_set_secret(key: str, value: str) -> None:
    region_name = getattr(settings, "AWS_REGION", "us-east-1")
    client = init_aws_client(region_name)
    client.create_secret(Name=key, SecretString=value)


# Azure Key Vault Secrets Manager

def init_azure_client(azure_vault_url: str):
    azure_identity = importlib.import_module("azure.identity")
    azure_keyvault = importlib.import_module("azure.keyvault.secrets")
    return azure_keyvault.SecretClient(
        vault_url=azure_vault_url,
        credential=azure_identity.DefaultAzureCredential()
    )


def azure_get_secret(key: str) -> str:
    azure_vault_url = getattr(settings, "AZURE_VAULT_URL")
    client = init_azure_client(azure_vault_url)
    secret = client.get_secret(key)
    return secret.value


def azure_set_secret(key: str, value: str) -> None:
    azure_vault_url = getattr(settings, "AZURE_VAULT_URL")
    client = init_azure_client(azure_vault_url)
    return client.set_secret(key, value)


# Google Cloud Secret Manager

def init_gcloud_client():
    secretmanager = importlib.import_module("google.cloud.secretmanager")
    return secretmanager.SecretManagerServiceClient()


def gcloud_get_secret(key: str) -> str:
    project_id = getattr(settings, "PROJECT_ID")
    client = init_gcloud_client()
    secret_name = f"projects/{project_id}/secrets/{key}/versions/latest"
    response = client.access_secret_version(name=secret_name)
    return response.payload.data.decode("UTF-8")


def gcloud_set_secret(key: str, value: str) -> None:
    project_id = getattr(settings, "PROJECT_ID")
    client = init_gcloud_client()
    secret = client.create_secret(
        parent=f"projects/{project_id}",
        secret_id=key,
        secret={"replication": {"automatic": {}}}
    )
    client.add_secret_version(
        parent=secret.name,
        payload={"data": value.encode("UTF-8")}
    )


# HashiCorp Vault

def read_existent_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"File is empty: {file_path}")
            return content
    except FileNotFoundError:
        raise OSError(f"File not found: {file_path}")
    except PermissionError:
        raise OSError(f"Permission denied when reading file: {file_path}")


def init_vault_client():
    hvac = importlib.import_module("hvac")
    token_file_path = os.path.expanduser("~/.vault-token")

    token = read_existent_file(token_file_path)
    if not token:
        log_and_raise_value_error(
            f"Vault token file {token_file_path} is missing."
        )
        print("Authenticate using `vault login`.")

    address_file_path = f"{settings.CONFIG_DIR}/vault-address"
    address = (
        read_existent_file(address_file_path)
        or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    )
    if not address:
        print(f"Vault address file {address_file_path} is missing.")
        print("Set 'VAULT_ADDR' or provide a vault-address file.")

    return hvac.Client(url=address, token=token)


def vault_get_secret(key: str) -> Any:
    try:
        client = init_vault_client()
        data = client.secrets.kv.v2.read_secret_version(path=key)
        return data["data"]["data"]["data"]
    except KeyError as e:
        log_and_raise_value_error(
            f"Unexpected key ({key}) or secret structure: {e}"
        )


def vault_set_secret(key: str, value: Any) -> None:
    client = init_vault_client()
    client.secrets.kv.v2.create_or_update_secret(
        path=key,
        secret={"data": value}
    )
