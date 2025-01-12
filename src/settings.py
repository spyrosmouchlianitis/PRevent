import os


# Local Flask server listens on
WEBHOOK_PORT = 8080

# For the GitHub client
JWT_EXPIRY_SECONDS = 120

# Block PR until approval. Respected only if reviewers were defined.
BLOCK_PR = True

# For branch protection rules
SCAN_CONTEXT = "apiiro-scan"

# Don't comment WARNING severity detections (many), only ERROR (few).
FP_STRICT = False

# Set TLS on another level if not here
APP_TLS = False

# Dir for storing log file, and if relevant: TLS certificates, Vault address
CONFIG_DIR = os.path.expanduser('~/.pr-event')
os.makedirs(CONFIG_DIR, exist_ok=True)

# Logging
INFO_LOG_FILE = f'{CONFIG_DIR}/info.log'
ERROR_LOG_FILE = f'{CONFIG_DIR}/error.log'

# Repos
APP_REPO = "https://github.com/apiiro/pr-event"
RULESET_REPO = "https://github.com/apiiro/malicious-code-ruleset"
RULESET_DIR = f'{CONFIG_DIR}/malicious-code-ruleset'

# Set to a remote service
SECRET_MANAGER = 'local'
