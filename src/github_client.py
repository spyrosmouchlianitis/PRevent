import jwt
import time
import requests
from github import Github
from fastapi.logger import logger
from src.secret_manager import get_secret
from src.settings import JWT_EXPIRY_SECONDS


def initialize_github_client() -> Github:
    jwt_token = create_jwt()
    installation_token = get_installation_token(jwt_token)
    return Github(installation_token)


def get_installation_token(jwt_token: str) -> str:
    headers = jwt_headers(jwt_token)
    installation_id = get_installation_id(headers)
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    response = requests.post(url, headers=headers)
    if response.status_code == 201:
        return response.json()['token']
    raise RuntimeError(f"Failed to get installation token: {response.status_code} {response.text}")


def get_installation_id(headers: dict) -> str:
    url = "https://api.github.com/app/installations"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        installations = response.json()
        if installations:
            return installations[0]['id']
        raise Exception("No installations found.")
    raise RuntimeError(f"Failed to fetch installations: {response.status_code} {response.text}")


def create_jwt() -> str:
    try:
        # Direct secrets use to minimize exposure in memory
        payload = {
            "iat": int(time.time()),
            "exp": int(time.time() + JWT_EXPIRY_SECONDS),
            "iss": str(get_secret("GITHUB_APP_INTEGRATION_ID"))
        }
        return jwt.encode(
            payload,
            get_secret("GITHUB_APP_PRIVATE_KEY"),
            algorithm="RS256"
        )
    except KeyError as e:
        logger.error(f"Missing secret key: {e}")
        raise
    except jwt.PyJWTError as e:
        logger.error(f"JWT encoding error: {e}")
        raise


def jwt_headers(jwt_token: str) -> dict:
    return {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }


def token_headers() -> dict:
    return {
        "Authorization": f"token {get_installation_token(create_jwt())}",
        "Accept": "application/vnd.github+json"
    }
