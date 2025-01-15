# Contributing to malicious-code-ruleset

Thank you for your interest in contributing! Please follow these simple steps to ensure a smooth contribution process.

---

## Workflow
1. **Fork and Clone**:
    ```bash
    git clone https://github.com/apiiro/malicious-code-ruleset.git
    cd malicious-code-ruleset
    ```
2. **Create a Branch**:
    ```bash
    git checkout -b rule/your-branch-name
    ```
3. **Make Changes**:
    - Add or improve Semgrep rules.
    - Write test cases.
    - Test using:
     ```bash
     semgrep --config ./malicious-code-ruleset
     ```
    - Test on at least 10 large repositories to ensure a low false-positive ratio.
    - If you add a new rule, make sure to set proper metadata. 
4. **Commit**:
    Write a clear, descriptive commit message:
    ```bash
    git commit -m "Add rule for detecting obfuscated eval in JavaScript"
    ```
5. **Push and Submit PR**:
    ```bash
    git push origin rule/your-branch-name
    ```
    - Provide a concise description in the pull request.

---

## Guidelines
- Follow [Semgrep Rule Writing Best Practices](https://semgrep.dev/docs/writing-rules/).
- Minimize false positives; prioritize precision.
- Add comments in YAML rules to explain detection logic.

---

## Reporting Issues
- Clearly describe the issue.
- Include a reproducible example if applicable.
- Submit via [GitHub Issues](https://github.com/apiiro/malicious-code-ruleset/issues).

---

## Licensing
By contributing, you agree to license your work under the [MIT License](LICENSE).

Thank you for helping improve Malicious-Code-Ruleset!
