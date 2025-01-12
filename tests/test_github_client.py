import jwt
from unittest.mock import patch
from src.github_client import create_jwt
from src.settings import JWT_EXPIRY_SECONDS


def test_create_jwt():
    with patch("time.time") as mock_time:
        mock_time.return_value = 1609459200  # Fixed mocked time
        token = create_jwt()
        decoded_token = jwt.decode(
            token,
            "test_private_key",
            algorithms=["RS256"],
            options={"verify_signature": False}
        )
        assert decoded_token["iat"] == 1609459200
        assert decoded_token["exp"] == 1609459200 + JWT_EXPIRY_SECONDS
        assert int(decoded_token["iss"]) > 9999
