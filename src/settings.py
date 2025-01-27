import os


# Options: vault, aws, azure, gcloud, local (vault)
SECRET_MANAGER = 'vault'

# Don't run WARNING severity detectors (many), run only ERROR severity detectors (few).
FP_STRICT = False

# Continue scanning after first detection
FULL_FINDINGS = False

# Block PR until approval. Respected only if reviewers were defined.
BLOCK_PR = True

# Local Flask server listens on
WEBHOOK_PORT = 8080

# For the GitHub client (minimum 10)
# Processing times exceeding the expiry time may result in unexpected behavior.
JWT_EXPIRY_SECONDS = 120

# For branch protection rules
SCAN_CONTEXT = "apiiro-scan"

# Set TLS on another level if not here
APP_TLS = False

# Dir for storing log file, and if relevant: Vault address, TLS certificates
CONFIG_DIR = os.path.expanduser('~/.prevent')
os.makedirs(CONFIG_DIR, exist_ok=True)

# Logging
INFO_LOG_FILE = f'{CONFIG_DIR}/info.log'
ERROR_LOG_FILE = f'{CONFIG_DIR}/error.log'

# Repos
APP_REPO = "https://github.com/apiiro/PRevent"
RULESET_REPO = "https://github.com/apiiro/malicious-code-ruleset"
