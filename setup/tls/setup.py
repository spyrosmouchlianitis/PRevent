import os
import sys
from setup.tls.settings import CERTS_DIR, PRIVATE_DIR, CERT_PATH, KEY_PATH
from setup.tls.validate_certs import validate_certificates
from setup.utils import get_host


def create_directories() -> None:
    os.makedirs(CERTS_DIR, mode=0o755, exist_ok=True)
    os.makedirs(PRIVATE_DIR, mode=0o700, exist_ok=True)

    print("\n")
    print("Directories created successfully:")
    print(f"  Certificates: {CERTS_DIR}")
    print(f"  Private Keys: {PRIVATE_DIR}")


def ensure_cert_and_key() -> None:
    print("\n")
    print("\033[1m### Certificate and Key Setup ###\033[0m")
    print("\n")
    is_public = input("Is the app running on a public domain? [Y/n]: ").strip().lower() or "y"
    if is_public == "y":
        print("\033[1m\nObtain a public TLS certificate from a trusted CA (e.g., Let's Encrypt): \033[0m")
        print("https://letsencrypt.org/getting-started/")
        host = get_host()
        if host:
            print(host)

    elif is_public == "n":
        print("If you have an internal org CA or an existing TLS certificate, use it.")
        is_org = input("Do you need to create a self-signed certificate? [Y/n]: ").strip().lower() or "y"
        if is_org == "y":
            print(f"openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\")
            print(f"-keyout {KEY_PATH} -out {CERT_PATH} \\")
            print(f"-subj \"/C=US/ST=None/L=None/O=PRevent/CN=localhost\"")
    
    print("\n")
    print("Save the certificates in the following paths:")
    print(f"  Certificate: {CERT_PATH}")
    print(f"  Private Key: {KEY_PATH}")
    
    print("\n")
    input("Press Enter once the files are saved as instructed...")

    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        print("\n")
        print("Error: One or both files are missing. Please verify the paths and try again.")
        sys.exit(1)

    # Set appropriate permissions. Modify according to your needs.
    try:
        os.chmod(CERT_PATH, 0o644)
        os.chmod(KEY_PATH, 0o600)
        print(f"\nFiles verified successfully:\n   Certificate: {CERT_PATH} (permissions: 644)\n   Key: {KEY_PATH} (permissions: 600)")
    except Exception as e:
        print(f"Error setting file permissions: {e}\nPlease set the permissions manually.")

    print("\n")
    print("Files verified successfully:")
    print(f"  Certificate: {CERT_PATH} (permissions: 644)")
    print(f"  Key: {KEY_PATH} (permissions: 600)")
    print("\n")
    print("For GitHub Enterprise, install the certificate on the server.")
    print("More details: https://docs.github.com/en/enterprise-server%403.11/admin/configuring-settings/hardening-security-for-your-enterprise/configuring-tls")
    
    print("\n")
    print("Notice that certificates have an expiry date that you set.")
    print("This is typically managed by a notification before the expiry date or an auto-renewal mechanism.")


def setup_tls() -> None:
    # Check if TLS is already configured
    if validate_certificates():
        print("TLS is already properly configured. Skipping TLS setup.")
        return
    
    print("\n")
    print("\033[1m### TLS Certificate Setup ###\033[0m")
    print("\n")

    create_directories()
    ensure_cert_and_key()

    if validate_certificates():
        print("\n")
        print("Setup complete! Your app is ready to use secure TLS.")
        print("\n")
    else:
        print("Certificates validation failed.")
        input("Press enter to rerun TLS setup, otherwise exit.")
        setup_tls()
