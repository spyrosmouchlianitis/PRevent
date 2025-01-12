#!/bin/bash

set -o errexit  # Exit on error
set -o pipefail # Fail on pipe errors
set -o nounset  # Fail on unset variables

# Check for required tools
command -v vault >/dev/null 2>&1 || { echo "Vault CLI not found"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq not found"; exit 1; }

# Ensure Vault is reachable
VAULT_ADDR="http://127.0.0.1:8200"
if ! curl -s "$VAULT_ADDR/v1/sys/health" > /dev/null; then
    echo "Vault is not running or accessible at $VAULT_ADDR"
    exit 1
fi

# Define sensitive files
VAULT_INIT_OUTPUT="$HOME/vault/vault_init.txt"

# Trap to clean up vault_init.txt on failure
trap 'rm -f "$VAULT_INIT_OUTPUT"' EXIT

# Initialize Vault if needed
VAULT_STATUS=$(curl -s "$VAULT_ADDR/v1/sys/health")
IS_INITIALIZED=$(echo "$VAULT_STATUS" | jq -r '.initialized')
IS_SEALED=$(echo "$VAULT_STATUS" | jq -r '.sealed')

if [ "$IS_INITIALIZED" == "false" ]; then
    echo "Vault is not initialized. Initializing Vault..."
    vault operator init > "$VAULT_INIT_OUTPUT" || { echo "Vault initialization failed."; exit 1; }
    ROOT_TOKEN=$(grep 'Initial Root Token:' "$VAULT_INIT_OUTPUT" | awk '{print $NF}')
    UNSEAL_KEYS=($(grep 'Unseal Key' "$VAULT_INIT_OUTPUT" | awk '{print $NF}'))
    echo "Vault initialized. Root token and unseal keys saved."
else
    echo "Vault is already initialized."
    ROOT_TOKEN=$(grep 'Initial Root Token:' "$VAULT_INIT_OUTPUT" | awk '{print $NF}')
    UNSEAL_KEYS=($(grep 'Unseal Key' "$VAULT_INIT_OUTPUT" | awk '{print $NF}'))
fi

# Validate ROOT_TOKEN
if [ -z "$ROOT_TOKEN" ]; then
    echo "Error: Root token not found."
    exit 1
fi

# Unseal Vault if needed
if [ "$IS_SEALED" == "true" ]; then
    echo "Vault is sealed. Unsealing Vault..."
    for key in "${UNSEAL_KEYS[@]}"; do
        vault operator unseal "$key" || { echo "Unseal failed for key: $key"; exit 1; }
    done
else
    echo "Vault is already unsealed."
fi

# Log in to Vault
vault login "$ROOT_TOKEN" || { echo "Failed to log in with root token."; exit 1; }

# Check if secrets engine exists and enable if not
SECRET_PATH="secret/"
if ! vault secrets list -format=json | jq -e ".\"$SECRET_PATH\"" > /dev/null; then
    echo "Enabling KV version 2 at '$SECRET_PATH'."
    vault secrets enable -path="$SECRET_PATH" kv-v2 || { echo "Failed to enable secrets engine."; exit 1; }
else
    echo "Secrets engine at '$SECRET_PATH' already exists."
fi

# Create policy if not exists
if ! vault policy read pr-event-app-policy > /dev/null 2>&1; then
    echo "Creating policy pr-event-app-policy."
    vault policy write pr-event-app-policy - <<EOF
path "secret/data/pr-event/*" {
    capabilities = ["create", "read", "update", "delete"]
}
EOF
else
    echo "Policy pr-event-app-policy already exists."
fi

# Enable AppRole if not already enabled
if ! vault auth list | grep -q 'approle'; then
    echo "Enabling AppRole authentication."
    vault auth enable approle || { echo "Failed to enable AppRole."; exit 1; }
fi

# Create or update AppRole
if ! vault read auth/approle/role/pr-event-app-role > /dev/null 2>&1; then
    echo "Creating AppRole pr-event-app-role."
    vault write auth/approle/role/pr-event-app-role token_policies="pr-event-app-policy" || { echo "Failed to create AppRole."; exit 1; }
else
    echo "AppRole pr-event-app-role already exists."
fi

# Generate credentials
ROLE_ID=$(vault read -field=role_id auth/approle/role/pr-event-app-role/role-id) || { echo "Failed to generate role_id"; exit 1; }
SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/pr-event-app-role/secret-id) || { echo "Failed to generate secret_id"; exit 1; }

echo "AppRole credentials: role_id=$ROLE_ID, secret_id=$SECRET_ID"

# Secure cleanup
rm -f "$VAULT_INIT_OUTPUT"
if [ ! -f "$VAULT_INIT_OUTPUT" ]; then
    echo "Successfully cleaned up sensitive files."
else
    echo "Failed to clean up sensitive files."
fi
