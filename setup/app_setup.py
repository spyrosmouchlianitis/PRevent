from src.secret_manager import set_secret
from src.settings import WEBHOOK_PORT
from src.config import rewrite_setting
from src.validation.config import validate_block_pr
from setup.utils import get_host, is_secret_set, validation_wrapper
from setup.setters import (
    set_webhook_port,
    set_webhook_secret,
    set_app_id,
    set_private_key,
    set_security_reviewers,
    set_branches_scope
)


# Secrets:
webhook_secret_key = 'WEBHOOK_SECRET'
app_id_key = 'GITHUB_APP_INTEGRATION_ID'
private_key_key = 'GITHUB_APP_PRIVATE_KEY'
security_reviewers_key = 'SECURITY_REVIEWERS'
branches_include_key = 'BRANCHES_INCLUDE'
branches_exclude_key = 'BRANCHES_EXCLUDE'
protected_branches_key = 'PROTECTED_BRANCHES'

# Other parameters:
webhook_port_key = 'WEBHOOK_PORT'
block_pr_key = 'BLOCK_PR'
fp_strict_key = 'FP_STRICT'


def set_github_app(secret_manager):
    
    # Basic info
    print("\n")
    print("Visit https://github.com/settings/apps to create a new GitHub App.")
    print("\033[1mSet the following fields: \033[0m")
    print("    GitHub App name: PR-event")
    print("    Write: Detects malicious code in pull requests.")
    print("    Homepage URL: https://github.com/apiiro/PR-event.git")
    input("\nPress Enter when you've completed this step.")

    # Webhook URL
    print("\n")
    print("Webhook URL:")
    print("    The URL where the app listens for PR events from GitHub.")
    print(f"    Locally, the current port is {WEBHOOK_PORT} (set in 'src/settings.py').")
    port = set_webhook_port(webhook_port_key)
    host = get_host()
    print(f"\n    Local webhook URL: https://{host}:{port}/webhook")
    print("\033[1m    Ensure the correct URL is set in GitHub, after verifying it's accessible.\033[0m")
    print("    Make sure to include the '/webhook' endpoint.")
    input("\nPress Enter when you've completed this step.")

    # Webhook secret
    print("\n")
    print("Webhook Secret:")
    if is_secret_set(webhook_secret_key):
        reset = input("Webhook secret is already set. Do you want to update? [y/N]: ") or 'n'
        if reset.strip().lower() == "y":
            set_webhook_secret(secret_manager, webhook_secret_key)
    else:
        print("    Verifies the authenticity of incoming payloads by checking their signature.")
        set_webhook_secret(secret_manager, webhook_secret_key)

    # App permissions
    print("\n")
    print("Between 3 to 5 permissions are required for the app's operation.")
    print("""
        During GitHub app setup, assign the following permissions:
            1. For PR scanning: read for data fetching, write for: commenting, triggering a review:
              \033[1mRepository Permissions: Pull requests -> Read and Write\033[0m
            2. For reading files with detections (and not just the PR diff): 
              \033[1mRepository Permissions: Contents -> Read-only\033[0m
            3. For creating commit statuses to monitor scan results:
              \033[1mRepository Permissions: Commit statuses -> Read and write\033[0m
            4. If you want to trigger reviews: referencing and listing teams and :
              \033[1mOrganization Permissions: Members -> Read-only\033[0m
            5. If you want to block on detection (manage branch protection):
              \033[1mRepository Permissions: Administration -> Read and write\033[0m
    """)
    print("Notice that to change the permissions later,")
    print("you will have to approve in your account settings after assigning them to the app.")
    input("\nPress Enter when you've completed this step.")

    # App events subscriptions
    print("\n")
    print("\033[1mIn 'Subscribe to events', select: \033[0m")
    print("    1. Pull request")
    print("    2. Pull request review")
    print("For \"Where can this GitHub App be installed?\", choose based on your preference.")
    input("\nCreate the app and press Enter.")

    # App ID
    print("\n")
    if is_secret_set(app_id_key):
        reset = input("App ID is already set. Do you want to update? [y/N]: ") or 'n'
        if reset.strip().lower() == "y":
            set_app_id(secret_manager, app_id_key)
    else:
        set_app_id(secret_manager, app_id_key)

    # App's private key
    print("\n")
    if is_secret_set(private_key_key):
        reset = input("Private key is already set. Do you want to update? [y/N]: ") or 'n'
        if reset.strip().lower() == "y":
            set_private_key(secret_manager, private_key_key)
    else:
        set_private_key(secret_manager, private_key_key)

    # Security reviewers
    print("\n")
    if is_secret_set(security_reviewers_key):
        reset = input("Security reviewers are already set. Do you want to update? [y/N]: ") or 'n'
        if reset.strip().lower() == "y":
            set_security_reviewers(secret_manager, security_reviewers_key)
    else:
        print("\033[1mDo you want to trigger code reviews upon detection?\033[0m")
        review = input("This is relevant regardless of detections blocking merging or not. [Y/n]: ") or "y"
        if review.strip().lower() == "y":
            set_security_reviewers(secret_manager, security_reviewers_key)

    # Block PR or not
    print("\n")
    print("\033[1mDo you want to block PR merging until a reviewer's approval is granted?\033[0m")
    print("Note: GitHub enabled private repos branch-protection only for Enterprise accounts.")
    block = input("[Y/n]: ") or "y"
    if block.strip().lower() == "y":
        validation_wrapper(validate_block_pr, block)
        rewrite_setting(block_pr_key, 'True')
        print(f"Successfully updated {block_pr_key} to True in 'src/settings.py'.")
    input("\nPress Enter when you've completed this step.")


    # Branches scope
    print("\n")
    if is_secret_set(branches_include_key) or is_secret_set(branches_exclude_key):
        reset = input("Branches scope is already set. Do you want to update? [y/N]: ") or 'n'
        if reset.strip().lower() == "y":
            set_branches_scope(secret_manager, branches_include_key, branches_exclude_key)
    else:
        print("After creating the app, go to 'Install App' and install for your desired accounts.")
        print("This is where you select which repositories will be protected by this app.")
        all_branches = input(
            "\033[1mDo you want to protect all branches of all selected repositories? [Y/n]: \033[0m"
        ) or "y"
        if all_branches.strip().lower() != "y":
            set_branches_scope(secret_manager, branches_include_key, branches_exclude_key)
        else:
            set_secret(branches_include_key, [])
            set_secret(branches_exclude_key, [])

    # Minimize FP
    print("\n")
    print("Few or no false positives are expected.")
    print("\033[1mDo you want to deprecate 'WARNING' severity detections (less coverage, less false-positives)?\033[0m")
    print(
        "Enter 'y' to run only 'ERROR' severity detectors (less frequent) "
        "and exclude 'WARNING' severity detectors."
    )
    print(
        "'ERROR' detections are typically related to dynamic execution, "
        "while 'WARNING' relates to obfuscation."
    )
    fp_strict = input("[y/N]: ") or "n"
    if fp_strict.strip().lower() == "y":
        rewrite_setting(fp_strict_key, 'True')
        print(f"Successfully updated {fp_strict_key} to True in 'src/settings.py'.")
    input("\nPress Enter when you've completed this step.")

    # Protected branches: a list of branches that were applied a branch protection rule
    if not is_secret_set(protected_branches_key):
        set_secret(protected_branches_key, {})
