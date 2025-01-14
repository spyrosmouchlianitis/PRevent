from typing import Dict, Any
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, current_app, request, Response, jsonify
from src.webhook import GitHubPRWebhook
from src.utils.webhook import verify_webhook_signature, check_rate_limit
from src.secret_manager import get_secret
from src.github_client import initialize_github_client
from setup.tls.settings import CERT_PATH, KEY_PATH
from src.settings import APP_TLS, WEBHOOK_PORT
from src.config import configure_logging


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)


@app.route('/webhook', methods=['POST'])
def webhook() -> tuple[Response, int]:
    event_type: str = request.headers.get('X-GitHub-Event', '')
    app.logger.info(f"Received event: {event_type}")

    try:
        # Ensure only GitHub's webhook deliveries are processed
        verify_webhook_signature(request)
        check_rate_limit(initialize_github_client())

        webhook_data: Dict[str, Any] = request.get_json() or {}
        webhook_listener = GitHubPRWebhook()

        return handle_event(event_type, webhook_listener, webhook_data)

    except Exception as e:
        current_app.logger.error(f"Error processing event {event_type}: {e}")
        return jsonify({"error": "Internal server error"}), 500


def handle_event(
    event_type: str,
    webhook_listener: GitHubPRWebhook,
    webhook_data: Dict[str, Any]
) -> tuple[Response, int]:
    if event_type == 'pull_request':
        webhook_listener.on_pull_request(webhook_data)
    elif event_type == 'pull_request_review' and get_secret('SECURITY_REVIEWERS'):
        webhook_listener.on_pull_request_review(webhook_data)
    return jsonify({"message": "Webhook received"}), 200


if __name__ == '__main__':

    configure_logging(app)

    if APP_TLS:
        app.run(
            port=WEBHOOK_PORT,
            debug=False,
            ssl_context=(CERT_PATH, KEY_PATH)
        )
    else:
        app.run(
            port=WEBHOOK_PORT,
            debug=False
        )
