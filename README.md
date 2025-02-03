# PRevent

A self-hosted GitHub app that listens for pull request events, scans them for malicious code, and comments detections directly on the pull request.

- [PRevent](#prevent)
  - [Why Use a GitHub Application](#why-use-a-github-application)
  - [Malicious Code Detection](#malicious-code-detection)
  - [Extra Capabilities](#extra-capabilities)
  - [Supported languages](#supported-languages)
- [Setup](#setup)
  - [Non-Containerized Setup](#non-containerized-setup)
  - [Containerized Setup](#containerized-setup)
    - [1. Secret Manager](#1-secret-manager)
      - [Secret Manager Setup Instructions](#secret-manager-setup-instructions)
    - [2. GitHub App](#2-github-app)
    - [3. Deployment](#3-deployment)
      - [Optional Parameters](#optional-parameters)
- [Docs](#docs)
- [Contributing](#contributing)
- [License](#license)


## Why Use a GitHub Application

Typically, security scans are run by workflow files. However, files can be modified, and when dealing with source modification attacks, should be avoided. A GitHub-app approach addresses this gap, ensuring the scan is not bypassed while providing better flexibility. 

The app's logic can be leveraged to run any scan. All you need is to add a scanner method to the [scan logic](https://github.com/apiiro/prevent/blob/main/src/scan/scan_logic.py).


## Malicious Code Detection

Currently, PRevent detects dynamic code execution and obfuscation, patterns found in nearly 100% of malicious code attacks reported to this day, while being rare in benign code, making the scan very effective. It uses Apiiro's [malicious-code-ruleset](https://github.com/apiiro/malicious-code-ruleset.git) for Semgrep, alongside additional Python-based detectors. Only rules and detectors with low false-positive rates are included. When a false-positive occurs, it's almost always due to poor coding practices.

![detection comment](https://github.com/user-attachments/assets/6c2d44ef-2967-4ed2-a69a-5ca89c38ea49)


## Extra Capabilities

Optional features:
- Select repositories and branches to include or exclude from the scan (default: all).
- Trigger code reviews from designated reviewers.
- Block merging until a reviewer's approval is granted or the scan passes.
- Run only the rules and detectors with the lowest false-positive rates.

Deployment:
- Supports containerization.
- Non-containerized deployment is fully automated with an interactive setup script.
- To manage GitHub key (required for any GitHub app), multiple secret managers are supported:
  - HashiCorp Vault
  - AWS Secrets Manager
  - Azure Key Vault
  - Google Cloud Secret Manager
  - Local HashiCorp Vault (for development and testing)

![merge blocking](https://github.com/user-attachments/assets/4abf58ce-90e9-4624-841b-b5d60bb8dcbb)


## Supported languages

- Bash
- Clojure
- C#
- Dart
- Go
- Java
- JavaScript
- TypeScript
- Lua
- PHP
- Python
- Ruby
- Rust
- Scala


# Setup

Deploying PRevent involves three parts, typically completed in 5 minutes to an hour, depending on your setup and familiarity:  
1. Configure an existing secret manager or create a new one.
2. Create a GitHub app within your GitHub Organization or account.
3. Deploy the application to a server.
4. If network access controls apply, the ["hooks" IP addresses](https://api.github.com/meta) should be allowed.

Use the latest Python version (3.9.2+ supported).


## Non-Containerized Setup

Parts 1 and 2 are handled during the interactive setup process in step 3:

1. Clone this repository:
   ```bash
   git clone https://github.com/apiiro/prevent.git
   cd prevent
   ```
2. Install dependencies by either poetry (recommended) or pip:  
   ```bash
   poetry install  
  
   pip install -r requirements.txt  
   ```
3. Go through the setup process:
   ```bash
   python3 -m setup.setup
   ```
4. Start the server:
   ```bash
   gunicorn --bind 0.0.0.0:8080 src.app:app 
   ```


## Containerized Setup

### 1. Secret Manager

The application communicates with GitHub via authenticated requests, which require three sensitive parameters:
- **Private Key** (`GITHUB_APP_PRIVATE_KEY`)
- **App ID** (`GITHUB_APP_INTEGRATION_ID`)
- **Webhook Secret** (`WEBHOOK_SECRET`)

To minimize security risks, these parameters should be stored in a secret manager with minimal permissions. Optionally, you may store additional sensitive details such as:
- **Repositories and branches** (`BRANCHES_INCLUDE`, `BRANCHES_EXCLUDE`)
- **Accounts and teams** (`SECURITY_REVIEWERS`)

The application handles all parameters exclusively through the secret manager (see supported managers below). In containerized deployments, this applies also for insensitive parameters, all are optional, for centralization and simplicity. Upon initialization, these parameters are written to `src/settings.py` to avoid repeated fetching during runtime. These include:
- **Block pull requests with detections** (`BLOCK_PR`)
- **False-positives rate strictness** (`FP_STRICT`)
- **Full scan instead of first detection only** (`FULL_FINDINGS`)
- **JWT token time-to-live** (`JWT_EXPIRY_SECONDS`)
- **Webhook listener's port** (`WEBHOOK_PORT`) - has to be manually updated in the Dockerfile


#### Secret Manager Setup Instructions

First, set **SECRET_MANAGER** in your secret manager to either: vault, aws, azure, gcloud, or local.

Dedicate a section in your secret manager for this app, separated from the rest. Create an app role with minimal permissions, to access the dedicated section only. If you are not sure how, try the following instructions:
```bash
python3 setup/secret_managers/print_instructions.py SECRET_MANAGER
```

Permissions required to operate the role:

| Permission | Vault                  | AWS                           | Azure                     | GCloud                    |
|------------|------------------------|-------------------------------|---------------------------|---------------------------|
| read       | read                   | secretsmanager:GetSecretValue | KeyVaultSecret:Get        | secretmanager.secrets.get | 
| write      | create, update         | secretsmanager:PutSecretValue | KeyVaultSecret:Set        | secretmanager.secrets.add |
| scope      | path = "prevent-app/*" | resource = "prevent-app/*"    | secret = "prevent-app/*"  | secret = "prevent-app/*"  |


### 2. GitHub App

1. Go to https://github.com/settings/apps to create a new GitHub App.
2. Set metadata:  
   - Name: prevent  
   - Description: Detects malicious code in pull requests.  
   - URL: https://github.com/apiiro/PRevent.git
3. Set the webhook URL: the address where the app will listen. Endpoint: `/webhook`. Examples:  
   - https://prevent.u.com/webhook  
   - https://10.0.0.7/webhook
4. Under the webhook URL field, set the secret field in order to process only requests originating from GitHub. You can run `python -c 'import secrets; print(secrets.token_hex(32))'` to generate one. Then, store it in your secrets manager as **WEBHOOK_SECRET**.
5. Set required permissions:
    
    | Parent     | Permission      | Action          | Reason                                                |
    |------------|-----------------|-----------------|-------------------------------------------------------|
    | Repository | Pull requests   | Read and Write  | Read PR, write comments (if enabled: trigger reviews) |
    | Repository | Commit statuses | Read and write  | Monitor scan-results by setting commits-statuses      |
    | Repository | Contents        | Read-only       | Get full files so AST can get built                   |

6. Set optional permissions:
    
    | Parent        | Permission     | Action          | Reason                   |
    |---------------|----------------|-----------------|--------------------------|
    | Repository    | Administration | Read and write  | Manage branch protection |

7. Subscribe to the following events:
   * `Pull request`
   * `Pull request review`

8. Click "Create GitHub App". Copy the App ID and store it in your secret manager as **GITHUB_APP_INTEGRATION_ID**.
9.  Generate a private key, store it in your secret manager as **GITHUB_APP_PRIVATE_KEY**, and make sure to delete the file.


### 3. Deployment

1. Set any desired optional parameters from below in your secret manager.
2. Follow the [Docker README](docker/README.md) to build, configure and register your container image.
3. Follow the [Helm README](helm/README.md) to package and deploy your container to your Kubernetes cluster according to best practices.


#### Optional Parameters

- **BLOCK_PR**: 
To block merging until either a reviewer approves the pull request or the scan passes, set it to `True` in your secret manager.

- **SECURITY_REVIEWERS**: 
To trigger code reviews upon detections, configure it in your secret manager with a Python list of reviewer accounts or teams (e.g., `['account1', 'account2', 'team:appsec']`). Ensure you run `json.dumps(security_reviewers)` or an equivalent method beforehand.

- **INCLUDE_BRANCHES** or **EXCLUDE_BRANCHES**:
To include or exclude specific repos and branches for monitoring, set either in your secret manager with a Python dictionary. 
Use `{'repo1': 'all'}` to include or exclude all repo's branches, or specify a list of branches (e.g., `{'repo1': ['main', 'branch2'], 'repo2': 'all'}`). 
Ensure you run `json.dumps(security_reviewers)` or an equivalent method beforehand. By default, all repositories and branches are monitored.

- **FP_STRICT**:
To minimize false-positives by running only `ERROR` severity rules and detectors (primarily a small subset of obfuscation detection), set it to `True` in your secret manager. Typically, the false-positives rate is negligible regardless of enabling this option.

- **FULL_FINDINGS**:
To maximize security and enable detection of all findings without stopping after the first detection, set it to `True` in your secret manager. While the false-positives rate may slightly increase, it generally remains negligible.


# Docs

[Here](docs) you can find architecture, sequence and code logic flow diagrams, and a configuration parameters summary.

# Contributing

Contributions are welcome through pull requests or issues.

# Known Limitations

- The app does not persist pull request states.
- Only files up to 1 MB are scanned.
- Files consisting of long single-line are excluded from scanning.
- Response time ranges from 600 milliseconds to 7 seconds, with an average of 1.8 seconds. Longer times occur when detectors are updated.

# License

This repository is licensed under the [MIT License](LICENSE).

---

For more information:
https://apiiro.com/blog/prevent-malicious-code
