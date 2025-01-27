import sys
from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import TerminalFormatter


def bold_text(text: str) -> str:
    return "\033[1m" + text + "\033[0m"


def print_instructions(manager):

    # HashiCorp Vault

    if manager == 'vault':
        print(bold_text("\n##### HashiCorp Vault Setup #####\n"))
        print(bold_text("Step 1: On the Vault server, create an AppRole and a policy for prevent:"))
        print(highlight("""
vault auth enable approle

vault policy write app-policy - <<EOF
path "secret/data/prevent/*" {
    capabilities = ["create", "read", "update", "delete"]
}
EOF

vault write auth/approle/role/app-role token_policies="prevent-app-policy"
        """, BashLexer(), TerminalFormatter()))
        print(bold_text(
            "\nStep 2: On the Vault server, generate AppRole credentials (role_id, secret_id):\n"
        ))
        print(highlight("""
vault read auth/approle/role/app-role/role-id

vault write -f auth/approle/role/app-role/secret-id
        """, BashLexer(), TerminalFormatter()))
        print(bold_text("\nStep 3: Return here to \"vault login\", or do it independently.\n\n"))

    # AWS Secrets Manager
    elif manager == 'aws':
        print(bold_text("\n##### AWS Secrets Manager Setup #####\n"))
        print(bold_text(
            "Step 1: Create an IAM Role for the specific application (e.g. prevent-app-role):"))
        print(highlight("""
aws iam create-role --role-name prevent-app-role --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Principal": { "Service": "sts.amazonaws.com" }
        }
    ]
}'
        """, BashLexer(), TerminalFormatter()))
        print(bold_text(
            "Step 2: Attach a policy granting least-privilege secrets access for the role:"))
        print(highlight("""
aws iam put-role-policy --role-name prevent-app-role \
--policy-name prEventAppSecretsPolicy --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:CreateSecret",
                "secretsmanager:PutSecretValue",
                "secretsmanager:DeleteSecret"
            ],
            "Resource": "arn:aws:secretsmanager:region:account-id:secret:prevent-secret-*"
        }
    ]
}'
        """, BashLexer(), TerminalFormatter()))
        print(bold_text("Step 3: Assume the role to retrieve temporary security credentials:"))
        print(highlight("""
aws sts assume-role \\ 
--role-arn arn:aws:iam::account-id:role/prevent-app-role \\
--role-session-name "prEventAppSession"
        """, BashLexer(), TerminalFormatter()))
        print(bold_text(
            "Step 4: Preferably, limit network access to this ARN to the app's IP, "
            "by a VPC policy:"
        ))
        print(bold_text(
            "\nStep 5: Either return here to insert the resulted credentials in \"aws configure\", "
            "or make sure to do it independently.\n\n"
        ))

    # Azure Key Vault
    elif manager == 'azure':
        print(bold_text("\n##### Azure Key Vault Setup #####\n"))
        print(bold_text(
            "Step 1: Create a managed identity specifically for the application "
            "(e.g. prevent-app-identity):"
        ))
        print(highlight(
            "az identity create --name prevent-app-identity --resource-group prevent-rg",
            BashLexer(), TerminalFormatter()
        ))
        print(bold_text(
            "Step 2: Grant least-privilege access to the managed identity "
            "for secrets in Azure Key Vault:"
        ))
        print(highlight("""
az keyvault set-policy --name prevent-keyvault \\
--object-id $(az identity show --name prevent-app-identity \\
--resource-group prevent-rg --query 'principalId' -o tsv) \\
--secret-permissions get list set delete --resource-id /secrets/prevent-secret-*
        """, BashLexer(), TerminalFormatter()))
        print(bold_text(
            "Step 3: Ensure network security by applying Key Vault firewall rules "
            "to allow access only from trusted sources:"
        ))
        print(highlight(
            "az keyvault network-rule add --name prevent-keyvault --ip-address <trusted-ip>",
            BashLexer(), TerminalFormatter()
        ))
        print(bold_text(
            "Step 4: Return here to \"az login\" and fill in the resulted credentials, "
            "or do it independently.)\n\n"
        ))

    # Google Cloud Secret Manager
    elif manager == 'gcloud':
        print(bold_text("\n##### Google Cloud Secret Manager Setup #####\n"))
        print(bold_text(
            "Step 1: Create and set a Google Cloud project for your application"
            "(e.g. prevent-app-project):\n"
        ))
        print(highlight("""
gcloud projects create prevent-app-project

gcloud config set project prevent-app-project
        """, BashLexer(), TerminalFormatter()))
        print(bold_text(
            "Step 2: Create a service account for the application (e.g. prevent-app-sa)"
            "and grant secret access:\n"
        ))
        print(highlight("""
gcloud iam service-accounts create prevent-app-sa --display-name "Service Account for prevent app"

gcloud projects add-iam-policy-binding prevent-app-project \\
--member "serviceAccount:prevent-app-sa@prevent-app-project.iam.gserviceaccount.com" \\
--role "roles/secretmanager.secretAccessor"
        """, BashLexer(), TerminalFormatter()))
        print(bold_text("Step 3: Generate and download the service account key."))
        print(highlight("""
gcloud iam service-accounts keys create prevent-app-sa-key.json \\
--iam-account prevent-app-sa@prevent-app-project.iam.gserviceaccount.com
        """, BashLexer(), TerminalFormatter()))
        print(bold_text(
            "Step 4: Return here to \"gcloud auth login\" and fill in the resulted credentials, "
            "or do it independently.\n\n"
        ))

    # Local HashiCorp Vault
    elif manager == 'local':
        print(bold_text("\n##### Local HashiCorp Vault Setup #####\n"))
        print(
            "*** To automate this, you can run " +
            bold_text("./setup/secret_managers/vault_local_config.sh")
        )
        print(bold_text(
            "\n\n1. Create a '~/vault/vault.hcl' config file with storage backend, "
            "listener, and unseal keys:"
        ))
        print(highlight("""
storage "file" {
    path = "~/vault/data"
}
listener "tcp" {
    address = "0.0.0.0:8200"
    cluster_address = "0.0.0.0:8201"
    tls_disable = 1  # local use
}
disable_mlock = true
        """, BashLexer(), TerminalFormatter()))
        print(bold_text("2. Start Vault:"))
        print(highlight(
            "vault server -config=$HOME/vault/vault.hcl",
            BashLexer(), TerminalFormatter()
        ))
        print(bold_text("3.1. Initialize Vault:"))
        print(highlight(
            "export VAULT_ADDR=\"http://127.0.0.1:8200\" && vault operator init",
            BashLexer(), TerminalFormatter()
        ))
        print(bold_text("3.2. Save the returned root token and unseal keys."))
        print(bold_text("\n4.1. Unseal Vault:"))
        print(highlight("vault operator unseal <unseal-key>", BashLexer(), TerminalFormatter()))
        print(bold_text("4.2. Repeat for the remaining unseal keys until Vault is unsealed."))
        print(bold_text("\n5. Enable the key-value secrets engine:"))
        print(highlight("vault secrets tune -version=2 secret/\n\n", BashLexer(), TerminalFormatter()))


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <manager>")
        print("vault, aws, azure, gcloud, local")
        sys.exit(1)
    print_instructions(sys.argv[1])


if __name__ == "__main__":
    main()
