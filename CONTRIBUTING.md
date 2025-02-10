# Contributing to PRevent

Thank you for your interest in contributing! 
Please follow these simple steps to ensure a smooth contribution process.

---

## Workflow
1. **Fork and Clone**:
    ```bash
    git clone https://github.com/apiiro/PRevent.git
    cd PRevent
    ```
2. **Create a Branch**:
    ```bash
    git checkout -b feature/branch-name
    ```
3. **Make Changes**:
    - Thoroughly test live with GitHub.
    - If your changes affect the scan, test on at least 3 large repositories and languages. 
    - If your changes affect the scan, ensure an extremely low false-positive rate is kept.
4. **Commit**:
    Commits must be signed.
    Write a clear, descriptive commit message:
    ```bash
    git commit -S -m "Added config parameters validation on container initialization"
    ```
5. **Push and Submit PR**:
    ```bash
    git push origin rule/your-branch-name
    ```
    - Provide a concise description in the pull request.

---

## Reporting Issues
- Make sure the issue isn't referenced in known-limitations.
- Make sure the issue doesn't exist already.
- Clearly describe the issue.
- Include a reproducible example if applicable.
- Submit via [GitHub Issues](https://github.com/apiiro/PRevent/issues).

---

## Licensing
By contributing, you agree to license your work under the [MIT License](LICENSE).

Thank you for helping improve PRevent!
