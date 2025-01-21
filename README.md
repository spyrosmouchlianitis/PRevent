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


# Setup

Deploying PRevent involves three parts, typically completed in 5 minutes to an hour, depending on your setup and familiarity:  
1. Configure an existing secret manager or create a new one.
2. Create a GitHub app within your GitHub organization or account.
3. Deploy the application to a server (supports both containerized and raw).


## 1. Secret Manager

The app communicates with GitHub using authenticated requests, requiring a private key and app ID. To minimize security risks, a secret manager should be used with minimal permissions. Optionally, other sensitive details (accounts, teams, repositories, branches) may be stored, while the rest of the configuration is minimal. To ensure centralization and simplicity, all parameters (3 required, 6 optional - see full list in a later section) are stored in the secret manager.

Supported secret managers:

* HashiCorp Vault
* AWS Secrets Manager
* Azure Key Vault
* Google Cloud Secret Manager
* Local HashiCorp Vault (for development/testing)

### Secret Manager Setup Instructions

Use a dedicated section in your secret manager for this app, separated from the rest. Use a dedicated role with minimal permissions, to access only the dedicated section. If you are not sure how, try the following instructions:
```bash
python3 setup/secret_managers/print_instructions.py SECRET_MANAGER
```
Replace SECRET_MANAGER with: vault, aws, azure, gcloud, or local.

Permissions required to operate your dedicated role (make sure to not assign anything else):

| Permission | Vault                  | AWS                           | Azure                     | GCloud                    |
|------------|------------------------|-------------------------------|---------------------------|---------------------------|
| read       | read                   | secretsmanager:GetSecretValue | KeyVaultSecret:Get        | secretmanager.secrets.get | 
| write      | create, update         | secretsmanager:PutSecretValue | KeyVaultSecret:Set        | secretmanager.secrets.add |
| scope      | path = "prevent-app/*" | resource = "prevent-app/*"    | secret = "prevent-app/*"  | secret = "prevent-app/*"  |


## 2. GitHub App

1. Go to https://github.com/settings/apps to create a new GitHub App.
2. Set metadata:  
   - Name: prevent  
   - Description: Detects malicious code in pull requests.  
   - URL: https://github.com/apiiro/PRevent.git
3. Set the webhook URL: the address where the app will listen. Endpoint: `/webhook`. Examples:  
   - https://prevent.u.com/webhook  
   - https://10.0.0.7/webhook
4. Under the webhook URL field, set the secret field in order to process only requests originating from GitHub. You can run `python -c 'import secrets; print(secrets.token_hex(32))'` to generate one. Then, store it in your secrets manager as `WEBHOOK_SECRET`.
5. Set required permissions:

| Parent     | Permission      | Action          | Reason                                                |
|------------|-----------------|-----------------|-------------------------------------------------------|
| Repository | Pull requests   | Read and Write  | Read PR, write comments (if enabled: trigger reviews) |
| Repository | Commit statuses | Read and write  | Monitor scan-results by setting commits-statuses      |
| Repository | Contents        | Read-only       | Get full files, can't build AST from diff             |

6. Set optional permissions:

| Parent        | Permission     | Action          | Reason                   |
|---------------|----------------|-----------------|--------------------------|
| Organization  | Members        | Read-only       | Trigger reviews          |
| Repository    | Administration | Read and write  | Manage branch protection |

7. Subscribe to the following events:
   1. `Pull request`
   2. `Pull request review`

8. Click "Create GitHub App". Copy the App ID and store it in your secret manager as `GITHUB_APP_INTEGRATION_ID`.
9. Generate a private key, store it in your secret manager as `GITHUB_APP_PRIVATE_KEY`, and make sure to delete the file.


## 3. Deployment

### Optional Parameters

1. `PR_BLOCK`: To block merging until either a reviewer approves the pull request or the scan passes, set it to `True` in your secret manager.
2. `SECURITY_REVIEWERS`: To trigger code reviews upon detections, configure it in your secret manager with a Python list of reviewer accounts or teams (e.g., `['account1', 'account2', 'team:appsec']`). Ensure you run `json.dumps(security_reviewers)` or an equivalent method beforehand.
3. `INCLUDE_BRANCHES` or `EXCLUDE_BRANCHES`: To include or exclude specific repos and branches for monitoring, set either in your secret manager with a Python dictionary. Use `{'repo1': 'all'}` to include or exclude all repo's branches, or specify a list of branches (e.g., `{'repo1': ['main', 'branch2'], 'repo2': 'all'}`). Ensure you run `json.dumps(security_reviewers)` or an equivalent method beforehand. By default, all repositories and branches are monitored.
4. `FP_STRICT`: To minimize false positives by running only `ERROR` severity rules and detectors (primarily a small subset of obfuscation detection), set it to `True` in your secret manager.


### Containerized Deployment

TODO: Add a CLEAR explanation on how to securely pass these to the container. Also, clarify and expand on anything else in this section that deserves it.

Credentials required to operate your dedicated app role: 

| Vault        | AWS                          | Azure                      | GCloud                              |
|--------------|------------------------------|----------------------------|-------------------------------------|
| VAULT_ADDR   | AWS_ACCESS_KEY_ID            | AZURE_CLIENT_ID            | GOOGLE_APPLICATION_CREDENTIALS_JSON | 
| VAULT_TOKEN  | AWS_SECRET_ACCESS_KEY        | AZURE_CLIENT_SECRET        | GOOGLE_CLOUD_PROJECT                |
|              | AWS_SESSION_TOKEN (optional) | AZURE_TENANT_ID (optional) | GOOGLE_CLOUD_REGION (optional)      |
|              |                              |                            | GOOGLE_API_KEY (optional)           |

1. Build the app using the provided `Dockerfile`:
```bash
docker buildx build -t prevent .
```
2. Push the image to your container registry (e.g. GCR):
```bash
PREVENT_TAG=1.0
docker buildx build \
  --platform linux/arm64/v8,linux/amd64 \
  --push --pull \
  -t us-docker.pkg.dev/user/public-images/prevent:$PREVENT_TAG \
  .
```
3. Run the container:
```bash
PREVENT_TAG=1.0
docker run --rm -it us-docker.pkg.dev/user/public-images/prevent:$PREVENT_TAG
```
4. Access the container:
``` bash
docker run --rm -it --entrypoint /bin/sh us-docker.pkg.dev/user/public-images/prevent:$PREVENT_TAG
```


### Manual Deployment

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


## Configuration Parameters Summary

| Parameter          | Name                      | Purpose                                             | source | Default |
|--------------------|---------------------------|-----------------------------------------------------|--------|---------|
| private key        | GITHUB_APP_PRIVATE_KEY    | Authenticates the app with GitHub                   | GitHub | -       |
| app ID             | GITHUB_APP_INTEGRATION_ID | Authenticates the app with GitHub                   | GitHub | -       |
| webhook secret     | WEBHOOK_SECRET            | Validates events are sent by GitHub                 | GitHub | -       |
| included branches  | BRANCHES_INCLUDE          | Branches to scan (all by default)                   | user   | {}      |
| exclude branches   | BRANCHES_EXCLUDE          | Branches to not scan                                | user   | {}      |
| security reviewers | SECURITY_REVIEWERS        | GitHub accounts and teams to review detections      | user   | []      |
| block merging      | BLOCK_PR                  | Block merging in pull requests with detections      | user   | False   |
| minimize FP        | FP_STRICT                 | Run only `ERROR` severity rules, exclude `WARNING`  | user   | False   |
| JWT expiry time    | JWT_EXPIRY_SECONDS        | Limit the app's GitHub auth token TTL               | user   | 120     |


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
