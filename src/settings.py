import os


# Local Flask server listens on
WEBHOOK_PORT = 8080

# For the GitHub client
JWT_EXPIRY_SECONDS = 120

# Don't comment WARNING severity detections (many), only ERROR (few).
FP_STRICT = False

# Block PR until approval. Respected only if reviewers were defined.
BLOCK_PR = True

# Set TLS on another level if not here
APP_TLS = False

# For branch protection rules
SCAN_CONTEXT = "apiiro-scan"

# Dir for storing log file, and if relevant: Vault address, TLS certificates
CONFIG_DIR = os.path.expanduser('~/.prevent')
os.makedirs(CONFIG_DIR, exist_ok=True)

# Logging
INFO_LOG_FILE = f'{CONFIG_DIR}/info.log'
ERROR_LOG_FILE = f'{CONFIG_DIR}/error.log'

# Repos
APP_REPO = "https://github.com/apiiro/PRevent"
RULESET_REPO = "https://github.com/apiiro/malicious-code-ruleset"

# Set to a remote service
SECRET_MANAGER = 'vault'
