import os
import shutil
import subprocess
import platform
import hashlib

base_dir = '/tmp'


def download_file(url: str, dest: str) -> None:
    subprocess.run(["curl", "-o", dest, url], check=True)


def verify_gpg_signature(file: str, signature: str) -> None:
    subprocess.run(["gpg", "--verify", signature, file], check=True)


def verify_checksum(file_path: str, expected_checksum: str) -> None:
    with open(file_path, "rb") as f:
        if hashlib.sha256(f.read()).hexdigest() != expected_checksum:
            raise ValueError(f"Checksum mismatch for {file_path}")


def update_shell_profile(bin_dir: str) -> None:
    shell_config_files = [
        "~/.bash_profile",
        "~/.bashrc",
        "~/.zshrc",
        "~/.profile",
        "~/.zprofile"
    ]
    line_to_add = f'export PATH="{bin_dir}:$PATH"'
    for shell_profile in shell_config_files:
        path = os.path.expanduser(shell_profile)
        if os.path.exists(path):
            with open(path, "r+") as file:
                lines = file.readlines()
                if line_to_add not in (line.strip() for line in lines):
                    file.write(f"\n{line_to_add}\n")


def cleanup(files: list[str]) -> None:
    for file in files:
        try:
            os.remove(file)
        except OSError:
            pass  # Ignore errors if file doesn't exist


def install_aws() -> None:
    try:
        version = "2.10.0"
        zip_url = f"https://awscli.amazonaws.com/awscli-exe-linux-x86_64-{version}.zip"
        sig_url = f"https://awscli.amazonaws.com/awscli-exe-linux-x86_64-{version}.zip.sig"
        gpg_file_name = "aws.gpg.sig"

        # Download files
        download_file(zip_url, "awscliv2.zip")
        download_file(sig_url, "awscliv2.zip.sig")

        # Amazon don't provide access to their optional GPG key,
        # to avoid supply chain security hazards caused by improper automation.
        # In this case, it's better than no check.
        gpg_file_base = os.path.dirname(os.path.abspath(__file__))
        gpg_file_path = f'{gpg_file_base}/{gpg_file_name}'

        # Import AWS GPG public key
        subprocess.run(["gpg", "--import", gpg_file_path], check=True)

        # Verify the GPG signature of the zip file
        verify_gpg_signature("awscliv2.zip", "awscliv2.zip.sig")

        # Extract the downloaded file
        subprocess.run(["unzip", "awscliv2.zip"], check=True)

        # Install AWS CLI locally for the user
        try:
            install_dir = os.path.expanduser("~/.aws-cli")
            subprocess.run(["./aws/install", "--install-dir", install_dir], check=True)

        except Exception as e:
            print(f"AWSCLI installation failed, probably due to permissions: {e}")
            sudo = input("Would you like to sudo it? [Y/n]: ").strip().lower() or "y"
            if sudo:
                try:
                    subprocess.run(["sudo", "./aws/install"], check=True)
                except Exception as e:
                    print(f"AWSCLI installation failed again: {e}")
                    print("Solve it manually and run setup.py again to continue the process from where you left.")
            else:
                print("Solve it manually and run setup.py again to continue the process from where you left.")

        finally:
            cleanup(["awscliv2.zip", "awscliv2.zip.sig", "aws/install"])

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def install_azure() -> None:
    try:
        # Use the official installation method
        install_script_url = "https://aka.ms/InstallAzureCli"

        # Download and execute the installation script
        subprocess.run(["curl", "-L", install_script_url, "|", "bash"], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def install_gcloud() -> None:
    arch = platform.machine()
    if arch == "arm64":
        arch = "arm"
    tar_url = f"https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-{arch}.tar.gz"
    tar_file = "google-cloud-cli.tar.gz"

    try:
        download_file(tar_url, tar_file)

        # Extract the tarball
        subprocess.run(["tar", "-xzf", tar_file], check=True)

        # Install gcloud CLI
        gcloud_dir = os.path.join(os.getcwd(), "google-cloud-sdk")
        install_script = os.path.join(gcloud_dir, "install.sh")
        subprocess.run([install_script, "--quiet"], check=True)

        # Update shell-profile with gcloud PATH
        bin_dir = os.path.join(gcloud_dir, "bin")
        update_shell_profile(bin_dir)

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        cleanup([tar_file])


def move_vault_to_bin(bin_dir: str) -> None:
    bin_path = os.path.join(bin_dir, "vault")
    subprocess.run(["mv", "vault", bin_path], check=True)


def extract_zip(zip_path: str) -> None:
    subprocess.run(["unzip", zip_path], check=True)


def install_vault() -> None:
    system = platform.system().lower()
    arch = platform.machine()
    version = "1.13.0"

    zip_file = os.path.join(base_dir, f"vault_{version}_{system}_{arch}.zip")
    checksum_file = os.path.join(base_dir, f"vault_{version}_SHA256SUMS")
    signature_file = os.path.join(base_dir, f"vault_{version}_SHA256SUMS.sig")
    gpg_file = os.path.join(base_dir, "vault_gpg.asc")

    zip_url = f"https://releases.hashicorp.com/vault/{version}/vault_{version}_{system}_{arch}.zip"
    checksum_url = f"https://releases.hashicorp.com/vault/{version}/vault_{version}_SHA256SUMS"
    signature_url = f"https://releases.hashicorp.com/vault/{version}/vault_{version}_SHA256SUMS.sig"
    gpg_key_url = "https://www.hashicorp.com/.well-known/pgp-key.txt"

    try:
        download_file(zip_url, zip_file)
        download_file(checksum_url, checksum_file)
        download_file(signature_url, signature_file)
        download_file(gpg_key_url, gpg_file)

        subprocess.run(["gpg", "--import", gpg_file], check=True)

        verify_gpg_signature(checksum_file, signature_file)

        with open(checksum_file, "r") as f:
            checksums = {line.split()[-1]: line.split()[0] for line in f if line.strip()}
        if os.path.basename(zip_file) not in checksums:
            raise ValueError(f"Checksum not found for {os.path.basename(zip_file)}")
        verify_checksum(zip_file, checksums[os.path.basename(zip_file)])

        extract_zip(zip_file)

        bin_dir = os.path.expanduser("~/bin")
        os.makedirs(bin_dir, exist_ok=True)
        move_vault_to_bin(bin_dir)

        update_shell_profile(bin_dir)

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        cleanup([zip_file, checksum_file, signature_file, gpg_file])


def is_sm_installed(manager: str) -> bool:
    valid_managers = ['vault', 'aws', 'azure', 'gcloud']
    if manager == 'local':
        manager = 'vault'
    if manager not in valid_managers:
        return False
    return shutil.which(manager) is not None


def install_sm(manager: str) -> None:
    install_methods = {
        'vault': install_vault,
        'aws': install_aws,
        'azure': install_azure,
        'gcloud': install_gcloud,
        'local': install_vault
    }
    install_methods.get(manager)()
