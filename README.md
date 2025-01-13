# PR-event

## Overview

The PR-event GitHub app listens for pull request events, scans diffs for malicious code, and posts detections directly on the pull request. It can trigger reviews from specified reviewers and block merging until either a reviewer's approval is granted or the scan passes. These features are independent, with the blocking mechanism enforced through a branch protection rule, without disrupting existing settings.

This app addresses a common security gap in workflow-based malware scans, where the attack vector is source code modification. It ensures that security workflows are not bypassed by repository write-access privileges. The app can be customized by modifying src.scan.scan_logic.handle_scan() to run different security scans.

## Malware Detection

Currently, PR-event detects dynamic code execution and obfuscation, patterns found in nearly 100% of malware-in-code attacks reported to this day. It uses Apiiro's [malicious-code-ruleset](https://github.com/apiiro/malicious-code-ruleset.git) for Semgrep, alongside additional Python-based detectors. Only rules and detectors with low false-positive rates are included. 

To run only the rules with the best impact to FP ratio, set `FP_STRICT` to `True` in `src/settings.py`. This will run only detectors and rules with severity set to `ERROR`.

## Installation & Setup

PR-event can be deployed on any server to support GitHub repositories, including both public and private repositories (via GitHub Enterprise for private repositories). The setup process is easy to follow and supports multiple secret managers for storing GitHub credentials.

### Steps
1. Clone this repository:
   ```bash
   git clone https://github.com/apiiro/pr-event.git
   cd pr-event
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

Alternatively, you can build and deploy the app using the provided `Dockerfile`.


## Contributing

Contributions are welcome through pull requests or issues.

## License

This repository is licensed under the [MIT License](LICENSE).

---

For more information:
https://apiiro.com/blog/pr-event-malicious-code
