import sys
import secrets
from getpass import getpass
from src.secret_manager import set_secret
from src.settings import WEBHOOK_PORT
from src.config import rewrite_setting
from setup.utils import validation_wrapper
from src.validation.config import (
    validate_webhook_port,
    validate_github_app_integration_id,
    validate_github_app_private_key,
    validate_webhook_secret,
    validate_branches,
    validate_security_reviewers
)


def set_webhook_port(webhook_port_key: str) -> int:
    try:
        port = input(
            "\033[1m    To change the port, enter a new value. Otherwise, press Enter: \033[0m"
        ) or WEBHOOK_PORT
        port = int(port)
        
        validate_webhook_port(port)
    
        if port != WEBHOOK_PORT:
            rewrite_setting(webhook_port_key, port)
            print(f"\n    Successfully updated {webhook_port_key} to {port} in 'src/settings.py'.")
            
        return port
    
    except Exception as e:
        print(f"\nWEBHOOK_PORT should be a valid port number: {e}")
        print("Try again")
        set_webhook_port(webhook_port_key)


def set_webhook_secret(secret_manager: str, webhook_secret_key: str) -> None:
    print("    Paste the same secret here and in GitHub.")
    print("    The secret will be saved in your secret manager.")
    print("    (verify inputs for typos, white-spaces and correct format)")
    
    random_secret = secrets.token_hex(32)
    print(f"\nAuto-generated secret: {random_secret}")
    
    webhook_secret = getpass(
        "\033[1mInsert your secret both here and in GitHub, "
        "or copy this secret into GitHub and press Enter (hidden): \033[0m"
    ) or random_secret
    
    if validation_wrapper(validate_webhook_secret, webhook_secret):
        set_secret(webhook_secret_key, webhook_secret)
        print(f"Successfully saved '{webhook_secret_key}' to your {secret_manager} secret manager.")
    else:
        print("Try again")
        set_webhook_secret(secret_manager, webhook_secret_key)
        
    input("\nPress Enter when you've completed this step.")


def set_app_id(secret_manager: str, app_id_key: str) -> None:
    print("(verify inputs for typos, white-spaces and correct format)")
    
    app_id = getpass(
        "\033[1mEnter the App ID to save it in your secret manager (hidden): \033[0m"
    ) or False
    
    if validation_wrapper(validate_github_app_integration_id, app_id):
        print(f"Successfully saved {app_id_key} in your {secret_manager} secret manager.")
        set_secret(app_id_key, app_id)
    else:
        print("Try again")
        set_app_id(secret_manager, app_id_key)

    input("\nPress Enter when you've completed this step.")
    

def set_private_key(secret_manager: str, private_key_key: str) -> None:
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
            validate_github_app_private_key(private_key)
    except FileNotFoundError:
        print(f"The specified path does not exist: {pk_path}. Try again")
        set_private_key(secret_manager, private_key_key)
    except Exception as e:
        print(e)
        again = input("Do you want to try again? [Y/n]: ") or "y"
        if again.strip().lower() == "y":
            set_private_key(secret_manager, private_key_key)
        else:
            sys.exit(1)
            
    set_secret(private_key_key, private_key)
    
    print(f"Successfully saved '{private_key_key}' in your {secret_manager} secret manager.")
    print("\n\033[1mDelete the private key file!\033[0m\n")
    print("In GitHub app setup, you can configure the IP allow list if relevant.")
    
    input("\nPress Enter when you've completed this step.")


def set_security_reviewers(secret_manager: str, security_reviewers_key: str) -> None:
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
            if again.strip().lower() == "y":
                get_reviewers()
            else:
                return []

    reviewers = get_reviewers() or []
    if validation_wrapper(validate_security_reviewers, reviewers):
        set_secret(security_reviewers_key, reviewers)
    
    print(
        f"Successfully saved '{security_reviewers_key}' as {reviewers} "
        f"in your {secret_manager} secret manager."
    )

    input("\nPress Enter when you've completed this step.")


def set_branches_scope(secret_manager: str, branches_include_key: str, branches_exclude_key: str) -> None:
    def list_branches() -> dict:
        print("(verify inputs for typos and correct format)")
        print("Format: repo_a:branch1,branch3 repo_b:all")
        all_repos_branches = {}
        while True:
            user_input = input("Repository and branches: ").strip()
            if not user_input:
                break
            pairs = user_input.split(" ")
            for pair in pairs:
                repo, repo_branches = pair.split(":")
                if repo_branches == 'all':
                    all_repos_branches[repo.strip()] = 'all'
                elif repo_branches:
                    all_repos_branches[repo.strip()] = [
                        b.strip() for b in repo_branches.split(",") if b.strip()
                    ]
            return all_repos_branches

    print("You can list branches for both inclusion and exclusion.")

    include = input("\033[1mDo you want to list branches for inclusion? [Y/n]: \033[0m") or "y"
    include_branches = list_branches() if include.strip().lower() == "y" else {}

    exclude = input("\033[1mDo you want to list branches for exclusion? [Y/n]: \033[0m") or "y"
    exclude_branches = list_branches() if exclude.strip().lower() == "y" else {}

    for branches, key in [
        (include_branches, branches_include_key), 
        (exclude_branches, branches_exclude_key)
    ]:
        if validation_wrapper(validate_branches, branches):
            set_secret(key, branches)
            print(f"Successfully saved '{key}' as {branches} "
                  f"in your {secret_manager} secret manager.")
        else:
            print("Try again")
            set_branches_scope(secret_manager, branches_include_key, branches_exclude_key)
            
    input("\nPress Enter when you've completed this step.")
