import os
import sys
import secrets
from getpass import getpass
from contextlib import redirect_stderr
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from src.secret_manager import get_secret, set_secret
from src.settings import WEBHOOK_PORT
from src.config import rewrite_setting
from setup.utils import get_host

# Secrets:
_webhook_secret = 'WEBHOOK_SECRET'
_app_id = 'GITHUB_APP_INTEGRATION_ID'
_private_key = 'GITHUB_APP_PRIVATE_KEY'
_security_reviewers = 'SECURITY_REVIEWERS'
_branches_include = 'BRANCHES_INCLUDE'
_branches_exclude = 'BRANCHES_EXCLUDE'
_protected_branches = 'PROTECTED_BRANCHES'


def is_secret_set(secret):
    try:
        with open(os.devnull, 'w') as hide, redirect_stderr(hide):
            get_secret(secret)
        return True
    except (ValueError, Exception):
        pass
    return False


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
    print(f"    Locally, the current port is {WEBHOOK_PORT} (set in './src/settings.py').")
    port = input(
        "\033[1m    To change the port, enter a new value. Otherwise, press Enter: \033[0m"
    ) or WEBHOOK_PORT
    if port != WEBHOOK_PORT:
        rewrite_setting('WEBHOOK_PORT', port)
        print(f"\n    Successfully updated 'WEBHOOK_PORT' to {port} in 'settings.py'.")
    host = get_host()
    print(f"\n    Local webhook URL: https://{host}:{port}/webhook")
    print("\033[1m    Ensure the correct URL is set in GitHub, after verifying it's accessible.\033[0m")
    print("    Make sure to include the '/webhook' endpoint.")
    input("\nPress Enter when you've completed this step.")

    # Webhook secret
    def set_webhook_secret() -> None:
        print("    Paste the same secret here and in GitHub.")
        print("    The secret will be saved in your secret manager.")
        print("    (verify inputs for typos, white-spaces and correct format)")
        random_secret = secrets.token_hex(32)
        print(f"\nAuto-generated secret: {random_secret}")
        webhook_secret = getpass(
            "\033[1mInsert your secret both here (hidden) and in GitHub, "
            "or copy this secret into GitHub and press Enter: \033[0m"
        ) or random_secret
        if not webhook_secret:
            print("An empty string was provided. Insert a valid secret.")
            set_webhook_secret()
        if len(webhook_secret) < 32:
            print("The secret has to be random and 32 characters or longer.\nInsert a valid secret.")
            set_webhook_secret()
        set_secret(_webhook_secret, webhook_secret)
        print(f"Successfully saved '{_webhook_secret}' to your {secret_manager} secret manager.")
        input("\nPress Enter when you've completed this step.")

    print("\n")
    print("Webhook Secret:")
    if is_secret_set(_webhook_secret):
        reset = input(
            "Webhook secret is already set. Do you want to update? [y/N]: "
        ).strip().lower() or 'n'
        if reset == "y":
            set_webhook_secret()
    else:
        print("    Verifies the authenticity of incoming payloads by checking their signature.")
        set_webhook_secret()

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
    def set_app_id() -> None:
        print("(verify inputs for typos, white-spaces and correct format)")
        app_id = getpass(
            "\033[1mEnter the App ID (hidden) to save it in your secret manager: \033[0m"
        ) or False
        if 10 > len(app_id) > 5:
            set_secret(_app_id, app_id)
            print(f"Successfully saved '{_app_id}' in your {secret_manager} secret manager.")
        else:
            print("A valid App ID is required to proceed.")
            set_app_id()
        input("\nPress Enter when you've completed this step.")

    print("\n")
    if is_secret_set(_app_id):
        reset = input(
            "App ID is already set. Do you want to update? [y/N]: "
        ).strip().lower() or 'n'
        if reset == "y":
            set_app_id()
    else:
        set_app_id()

    # App's private key
    def set_private_key() -> None:
        print("(verify inputs for typos, white-spaces and correct format)")
        print("Click 'Generate a private key' in GitHub, save the file.")
        pk_path = input(
            "\033[1mInsert the private key's file full path "
            "to save its content in your secret manager: \033[0m"
        ) or ""
        if not pk_path:
            pk_path = input(
                "Private key is required to proceed. Please enter its file's path to continue: "
            ) or ""
            if not pk_path:
                print("No private key provided. Please run the setup again when you're ready.")
                sys.exit(1)
        try:
            with open(pk_path, "r") as key_file:
                private_key = key_file.read()
                serialization.load_pem_private_key(
                    private_key.encode(),
                    password=None,
                    backend=default_backend()
                )
        except FileNotFoundError:
            print(f"The specified path does not exist: {pk_path}")
            print("Try again\n")
            set_private_key()
        except Exception as e:
            print(f"Error reading private key file {pk_path}: {e}")
            again = input("Do you want to exit or try again? [Y/n]: ") or "y"
            if again == "y":
                set_private_key()
            else:
                sys.exit(1)
        set_secret(_private_key, private_key)
        print(f"Successfully saved '{_private_key}' in your {secret_manager} secret manager.")
        print("\n\033[1m! DELETE THE PRIVATE KEY FILE !\033[0m\n")
        print("In GitHub app setup, you can configure the IP allow list if relevant.")
        input("\nPress Enter when you've completed this step.")

    print("\n")
    if is_secret_set(_private_key):
        reset = input(
            "Private key is already set. Do you want to update? [y/N]: "
        ).strip().lower() or 'n'
        if reset == "y":
            set_private_key()
    else:
        set_private_key()

    # Security reviewers
    def set_security_reviewers() -> None:
        def get_reviewers() -> list:
            try:
                print("Enter reviewer account or teams.")
                print("For teams, list as 'team:team_id' to include all members.")
                print("Format: account1, account2, team:devsecops, etc.")
                print("(verify inputs for typos and correct format)")
                security_reviewers = []
                while True:
                    user_input = input("Reviewers: ").strip()
                    if not user_input:
                        break
                    security_reviewers.extend([r.strip() for r in user_input.split(",")])
                return security_reviewers
            except Exception as e:
                print(f"Error getting reviewers: {e}")
                again = input(
                    "Do you want to try again? 'y' to try again, 'n' to skip [Y/n]: "
                ) or "y"
                if again == "y":
                    get_reviewers()
                else:
                    return []

        reviewers = get_reviewers() or []
        set_secret(_security_reviewers, reviewers)
        print(
            f"Successfully saved '{_security_reviewers}' as {reviewers} "
            f"in your {secret_manager} secret manager."
        )

    print("\n")
    if is_secret_set(_security_reviewers):
        reset = input(
            "Security reviewers are already set. Do you want to update? [y/N]: "
        ).strip().lower() or 'n'
        if reset == "y":
            set_security_reviewers()
    else:
        print("\033[1mDo you want to trigger code reviews upon detection?\033[0m")
        review = input(
            "This is relevant regardless of detections blocking merging or not. [Y/n]: "
        ).strip().lower() or "y"
        if review == "y":
            set_security_reviewers()

    input("\nPress Enter when you've completed this step.")

    # Block PR or not
    print("\n")
    print("\033[1mDo you want to block PR merging until a reviewer's approval is granted?\033[0m")
    print("Note: GitHub enabled private repos branch-protection only for Enterprise accounts.")
    block = input("[Y/n]: ").strip().lower() or "y"
    if block == "y":
        rewrite_setting('BLOCK_PR', 'True')
        print("Successfully updated 'BLOCK_PR' to 'True' in 'settings.py'.")

    input("\nPress Enter when you've completed this step.")

    # Branches scope
    def set_branches_scope() -> None:
        def list_branches() -> list:
            print("Format: repo_name:branch1,branch2 (leave empty for all).")
            print("Press Enter once to finish.")
            print("(verify inputs for typos and correct format)")
            branches = {}
            while True:
                user_input = input("Repository and branches: ").strip()
                if not user_input:
                    break
                repo, *branches = user_input.split(":")
                branches[repo.strip()] = [
                    b.strip() for b in branches[0].split(",") if b.strip()
                ] if branches else []
            return branches

        print("You can list branches for both inclusion and exclusion.")

        include = input(
            "\033[1mDo you want to list branches for inclusion? [Y/n]: \033[0m"
        ).strip().lower() or "y"
        include_branches = list_branches() if include == "y" else []

        exclude = input(
            "\033[1mDo you want to list branches for exclusion? [Y/n]: \033[0m"
        ).strip().lower() or "y"
        exclude_branches = list_branches() if exclude == "y" else []

        set_secret(_branches_include, include_branches)
        print(
            f"Successfully saved '{_branches_include}' as {include_branches} "
            f"in your {secret_manager} secret manager."
        )

        set_secret(_branches_exclude, exclude_branches)
        print(
            f"Successfully saved '{_branches_exclude}' as {exclude_branches} "
            f"in your {secret_manager} secret manager.")

        input("\nPress Enter when you've completed this step.")

    print("\n")
    if is_secret_set(_branches_include) or is_secret_set(_branches_exclude):
        reset = input(
            "Branches scope is already set. Do you want to update? [y/N]: "
        ).strip().lower() or 'n'
        if reset == "y":
            set_branches_scope()
    else:
        print("After creating the app, go to 'Install App' and install for your desired accounts.")
        print("This is where you select which repositories will be protected by this app.")
        all_branches = input(
            "\033[1mDo you want to protect all branches of all selected repositories? [Y/n]: \033[0m"
        ).strip().lower() or "y"
        if all_branches != "y":
            set_branches_scope()
        else:
            set_secret(_branches_include, [])
            set_secret(_branches_exclude, [])

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
    fp = input("[y/N]: ").strip().lower() or "n"
    if fp == "y":
        rewrite_setting('FP_STRICT', 'True')
        print("Successfully updated 'FP_STRICT' to 'True' in 'settings.py'.")

    input("\nPress Enter when you've completed this step.")

    # Protected branches: a list of branches that were applied a branch protection rule
    if not is_secret_set(_protected_branches):
        set_secret(_protected_branches, {})
