from setup.secret_managers.install_cli import is_sm_installed, install_sm
from setup.secret_managers.is_configured import is_sm_configured
from setup.secret_managers.configure_cli import (
    configure_sm,
    choose_secrets_manager,
    manage_secret_manager_dependency
)
from setup.app_setup import set_github_app
from setup.tls.setup import setup_tls
from src.config import rewrite_setting


def main():

    # Choose a secret manager to manage GitHub access keys and metadata
    secret_manager = choose_secrets_manager()
    print(f"Using {secret_manager} as a secret manager.")
    
    # Make sure the secret manager's CLI client is installed
    if not is_sm_installed(secret_manager):
        input(f"Press Enter to install {secret_manager} CLI client.")
        install_sm(secret_manager)

    # Make sure the secret manager's CLI client is configured
    if not is_sm_configured(secret_manager):
        input(f"Press Enter to configure {secret_manager} CLI client.")
        configure_sm(secret_manager)
    
    # Install the secret manager's Python package
    manage_secret_manager_dependency(secret_manager)

    # Remember the chosen secret manager
    rewrite_setting('SECRET_MANAGER', f"'{secret_manager}'")

    # Set up the GitHub app and its secrets
    set_github_app(secret_manager)

    # App level TLS
    prompt = "\033[1mDo you want to setup TLS in the app level? [y/N]: \033[0m"
    tls_step = input(prompt).strip().lower() or "n"
    if tls_step == "y":
        setup_tls()
    else:
        print("Make sure you setup TLS on another level (container, endpoint, gateway, etc.)")
        rewrite_setting('APP_TLS', 'False')

    print("\nSetup completed; the app is ready for use.")


if __name__ == "__main__":
    main()
