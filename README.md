# PRevent


## Overview

A self-hosted GitHub app that listens for pull request events, scans diffs for malicious code, and posts detections directly on the pull request.

Typically, security scans are run by workflow files. Files can be modified, and when dealing with source modification attacks, should be avoided. A GitHub app approach addresses this gap, ensuring the scan is not bypassed. The app's logic can be leveraged to run any scan. All you need is to add a scanner method to the [scan logic](https://github.com/apiiro/prevent/blob/main/src/scan/scan_logic.py).


## Malware Detection

Currently, PRevent detects dynamic code execution and obfuscation, patterns found in nearly 100% of malicious code attacks reported to this day, while being rare in benign code, making the scan very effective. It uses Apiiro's [malicious-code-ruleset](https://github.com/apiiro/malicious-code-ruleset.git) for Semgrep, alongside additional Python-based detectors. Only rules and detectors with low false-positive rates are included. 


## Extra Capabilities

Optional features:
- Granular selection of repositories and branches to include or exclude from the scan.
- Trigger code reviews from designated reviewers.
- Block merging until a reviewer's approval is granted or the scan passes.
- Run only the rules and detectors with the lowest false-positive rates.

Deployment:
- Supports containerization with a Dockerfile, Helm chart, and [TODO: complete description].
- Manual installation is fully automated via an interactive setup script.
- Multiple secret managers supported for managing the GitHub key (required for any GitHub app):
  - HashiCorp Vault
  - AWS Secrets Manager
  - Azure Key Vault
  - Google Cloud Secret Manager
  - Local HashiCorp Vault (for development and testing)


## Containerized Deployment 

Build and deploy the app using the provided `Dockerfile`.

First, you'll have to set a secret manager section for this app. If you are not sure how to do it, run:
```bash
python3 setup/secret_managers/print_instructions.py {vault|aws|azure|gcloud|local}
```

Then, create a GitHub app in GitHub:
1. Go to https://github.com/settings/apps to create a new GitHub App.
2. Set metadata:  
   - Name: prevent  
   - Description: Detects malicious code in pull requests.  
   - URL: https://github.com/apiiro/PRevent.git
3. Set the webhook URL: the address where the app will listen. Endpoint: `/webhook`. Examples:  
   - https://prevent.u.com/webhook  
   - https://10.0.0.7/webhook
4. Set required permissions:

| Parent     | Permission      | Action          | Reason                                                |
|------------|-----------------|-----------------|-------------------------------------------------------|
| Repository | Pull requests   | Read and Write  | Read PR, write comments (if enabled: trigger reviews) |
| Repository | Commit statuses | Read and write  | Monitor scan-results by setting commits-statuses      |
| Repository | Contents        | Read-only       | Get full files, can't build AST from diff             |

5. Set optional permissions:

| Parent        | Permission     | Action          | Reason                   |
|---------------|----------------|-----------------|--------------------------|
| Organization  | Members        | Read-only       | Trigger reviews          |
| Repository    | Administration | Read and write  | Manage branch protection |

6. Subscribe to the following events:
   1. Pull request
   2. Pull request review

7. Click "Create GitHub App". Copy the App ID and store it in your secret manager as "GITHUB_APP_INTEGRATION_ID".
8. Generate a private key, store it in your secret manager as "GITHUB_APP_PRIVATE_KEY", and delete the file (!).

TODO: Write this part when containerized deployment orchestration is ready (DevOps).  
Lastly, optionally configure security reviewers, included branches, and excluded branches.


## Manual Deployment

1. Clone this repository:
   ```bash
   git clone https://github.com/apiiro/prevent.git
   cd prevent
   ```
2. Install dependencies (Semgrep installation takes a moment):

   Using Poetry:
   ```bash
   poetry install
   ```

   Using pip:
   ```bash
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
5. For dev and testing:
   ```bash
   python3 -m src.app 
   ```

## Configuration Parameters

| Parameter           | Name                      | Purpose                                             | source | Storage         | Default |
|---------------------|---------------------------|-----------------------------------------------------|--------|-----------------|---------|
| private key         | GITHUB_APP_PRIVATE_KEY    | Authenticates the app with GitHub                   | GitHub | secret manager  | -       |
| app ID              | GITHUB_APP_INTEGRATION_ID | Authenticates the app with GitHub                   | GitHub | secret manager  | -       |
| webhook secret      | WEBHOOK_SECRET            | Validates events are sent by GitHub                 | GitHub | secret manager  | -       |
| included branches   | BRANCHES_INCLUDE          | Branches to scan (all by default)                   | user   | secret manager  | {}      |
| branches exclude    | BRANCHES_EXCLUDE          | Branches to not scan                                | user   | secret manager  | {}      |
| security reviewers  | SECURITY_REVIEWERS        | GitHub accounts and teams to review detections      | user   | secret manager  | []      |
| secret manager type | SECRET_MANAGER            | Defines the secret manager service in use           | user   | src/settings.py | vault   |
| block merging       | BLOCK_PR                  | Block merging in pull requests with detections      | user   | src/settings.py | False   |
| minimize FP         | FP_STRICT                 | Run only `ERROR` severity rules, exclude `WARNING`  | user   | src/settings.py | False   |
| JWT expiry time     | JWT_EXPIRY_SECONDS        | Limit the app's GitHub auth token TTL               | user   | src/settings.py | 120     |  


## Supported languages

Bash
Clojure
C#
Dart
Go
Java
JavaScript
TypeScript
Lua
PHP
Python
Ruby
Rust
Scala


## Contributing

Contributions are welcome through pull requests or issues.

## License

This repository is licensed under the [MIT License](LICENSE).

---

For more information:
https://apiiro.com/blog/prevent-malicious-code
