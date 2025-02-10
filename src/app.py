from typing import Any
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.logger import logger
from src.webhook import GitHubPRWebhook
from src.utils.webhook import verify_webhook_signature, check_rate_limit
from src.secret_manager import get_secret
from src.github_client import initialize_github_client
from setup.tls.settings import CERT_PATH, KEY_PATH
from src.settings import APP_TLS, WEBHOOK_PORT
from src.config import configure_logging
import uvicorn


app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    try:
        # Ensure only GitHub's webhook's requests are processed
        await verify_webhook_signature(request)
        check_rate_limit(initialize_github_client())

        event_type: str = request.headers.get('X-GitHub-Event', '')
        logger.info(f"Received event: {str(event_type)}")

        webhook_data: dict[str, Any] = await request.json()
        webhook_listener = GitHubPRWebhook()

        return handle_event(event_type, webhook_listener, webhook_data)

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def handle_event(
    event_type: str,
    webhook_listener: GitHubPRWebhook,
    webhook_data: dict[str, Any]
) -> tuple[Response, int]:
    if event_type == 'pull_request':
        webhook_listener.on_pull_request(webhook_data)
    elif event_type == 'pull_request_review' and get_secret('SECURITY_REVIEWERS'):
        webhook_listener.on_pull_request_review(webhook_data)
    return JSONResponse(content={"message": "Webhook received"}, status_code=200)


@app.get("/health")
def health():
    return JSONResponse(content={}, status_code=200)


if __name__ == "__main__":
    configure_logging()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        ssl_certfile=CERT_PATH if APP_TLS else None,
        ssl_keyfile=KEY_PATH if APP_TLS else None,
        log_level="debug",
        reload=True,
    )
