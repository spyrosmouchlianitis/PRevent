import toml
import subprocess
import importlib.metadata
from getpass import getpass
from setup.secret_managers.print_instructions import print_instructions
from src.settings import CONFIG_DIR
from src.config import write_setting


# Vault is used for two options, remote and local
def configure_vault(local=False):
    print("Configuring access: executing `vault login` (temporarily leaving the script)")
    try:
        subprocess.run(["vault", "login"], check=True)
        print("(verify inputs for typos, white-spaces and correct format)")
        if local:
            address = getpass(
                "Insert you Vault server address: ['http://127.0.0.1:8200']\n"
            ) or 'http://127.0.0.1:8200'
        else:
            address = getpass("Insert you Vault server address: ") or ''
        if address:
            vault_url_path = f"{CONFIG_DIR}/vault-address"
            with open(vault_url_path, 'w') as f:
                f.write(address)
            print(f"Successfully written Vault address to {vault_url_path}")
        else:
            print("No Vault address was received.")
            print("It's possible to define the env var VAULT_ADDR instead,")
            print("but it might not persist.")
        print("Vault access configured successfully.")
    except subprocess.CalledProcessError:
        print("Failed to login to Vault.")
        print("Ensure Vault CLI is installed, login, and rerun setup.py to continue")


def configure_aws():
    print("Configuring access: executing `aws configure` (temporarily leaving the script)")
    try:
        subprocess.run(["aws", "configure"], check=True)
        print("AWS Secrets Manager access configured successfully.")
        region = input("Insert region (verify inputs for typos and correct format): ") or ''
        if region:
            write_setting('AWS_REGION', f"'{region}'")
            print(f"Successfully saved 'AWS_REGION as {region} in 'settings.py'.")
        else:
            print("Region is required for AWS API requests to succeed.")
            print("Please add 'AWS_REGION = your_region' to 'setting.py' manually or run again.")
    except subprocess.CalledProcessError:
        print("Failed to configure AWS CLI.")
        print("Ensure it's installed, configure it, and rerun setup.py to continue")


def configure_azure():
    print("Configuring access: executing `az login` (temporarily leaving the script)")
    try:
        subprocess.run(["az", "login"], check=True)
        print("Azure Key Vault access configured successfully.")
        print("verify inputs for typos and correct format: https://<vault-name>.vault.azure.net/")
        azure_vault_url = input("Insert the URL of your Azure's vault: ") or ''
        if azure_vault_url:
            write_setting('AZURE_VAULT_URL', f"'{azure_vault_url}'")
            print(f"Successfully saved 'AZURE_VAULT_URL as {azure_vault_url} in 'settings.py'.")
    except subprocess.CalledProcessError:
        print("Failed to configure Azure access.")
        print("Ensure it's installed, configure it, and rerun setup.py to continue")


def configure_gcloud():
    print("Configuring access: executing `gcloud auth login` (temporarily leaving the script)")
    try:
        subprocess.run(["gcloud", "auth", "login"], check=True)
        print("Google Cloud Secret Manager access configured successfully.")
        project_id = input(
            "Insert the project ID you've created: ['PRevent-app-project']: "
        ) or 'PRevent-app-project'
        if project_id:
            write_setting('GCLOUD_PROJECT_ID', f"'{project_id}'")
            print(f"Successfully saved 'GCLOUD_PROJECT_ID as {project_id} in 'settings.py'.")
    except subprocess.CalledProcessError:
        print("Failed to configure Google Cloud access.")
        print("Ensure it's installed, configure it, and rerun setup.py to continue")


def configure_sm(manager: str):
    config_map = {
        "vault": configure_vault,
        "aws": configure_aws,
        "azure": configure_azure,
        "gcloud": configure_gcloud,
        "local": lambda: configure_vault(local=True),
    }
    config_map.get(manager, lambda: None)()


def poetry_install_if_missing(package: str) -> None:
    package_name, package_version = package.split("@")

    try:
        installed_version = importlib.metadata.version(package_name)
        if installed_version >= package_version:
            return

        update = input(
            f"A newer version of {package_name} is available."
            f"Do you want to update to version {package_version}? (y/n): ").strip().lower()
        if update == 'y':
            subprocess.run(["poetry", "add", package], check=True)
    
    except importlib.metadata.PackageNotFoundError:
        # Package is not installed, install it
        subprocess.run(["poetry", "add", package], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing package {package_name}: {e}")


def add_to_toml(package: str) -> None:
    package_name, package_version = package.split("@")
    addition = {package_name: package_version}

    with open("pyproject.toml", "r") as toml_file:
        data = toml.load(toml_file)

    dependencies = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    if package_name in dependencies:
        return

    dependencies.update(addition)
    with open("pyproject.toml", "w") as toml_file:
        toml.dump(data, toml_file)


# Install the secret manager's Python package, and add it to pyproject.toml
def manage_secret_manager_dependency(manager: str) -> None:
    dependencies = {
        "vault": "hvac@2.3.0",
        "aws": "boto3@1.35.97",
        "azure": "azure-keyvault-secrets@4.9.0",
        "gcloud": "google-cloud-secret-manager@2.22.0",
        "local": "hvac@2.3.0"
    }
    package: str = dependencies.get(manager)
    if package:
        poetry_install_if_missing(package)
        add_to_toml(package)


def choose_secrets_manager() -> str:
    print("During installation, you will configure your GitHub account with this app.")
    print("You will need to provide app credentials for GitHub verification.")
    print("You might also provide branch and account names for optional features.")
    print("Use a secret manager to store credentials securely.")
    print("This app can install a local manager for you (option 5).")
    print("However, it's highly recommended to use a remote secret manager.\n")
    print("Select the secret sm you use:")
    print("1) HashiCorp Vault")
    print("2) AWS Secrets Manager")
    print("3) Azure Key Vault Secrets")
    print("4) Google Cloud Secret Manager")
    print("5) Easy local storage with HashiCorp Vault (insecure)")

    choice = input("Enter the number corresponding to your choice: ")

    try:
        choice = int(choice)
        if choice not in range(1, 6):
            raise ValueError
    except ValueError:
        print("Invalid choice. Please run the script again and select a valid option.")
        return choose_secrets_manager()

    sm_types = {
        1: "vault",
        2: "aws",
        3: "azure",
        4: "gcloud",
        5: "local"
    }

    manager = sm_types[choice]
    print_instructions(manager)
    return manager
