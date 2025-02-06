# PRevent Helm Chart

## Step 1 - prerequisites

Create a namespace for the PRevent helm chart:

```shell
kubectl create namespace <namespace>
```

Create a Kubernetes secret for your secret manager credentials.
Choose one of the following:

### Kubernetes

It's a best practice to use a secrets manager, but you can choose Kubernetes Secrets.
Store all [parameters](/docs/DOCS.md) with sensitivity of medium and above in it. 
Low sensitivity parameters are configured in [values.yaml](values.yaml).

```shell
kubectl create secret generic k8s-credentials \
  --from-literal=github-app-private-key=<github-app-private-key-value> \
  --from-literal=github-app-integration-id=<github-app-integration-id-value> \
  --from-literal=webhook-secret=<webhook-secret-value> \
  # optional
  --from-literal=branches-include=<branches-include-value> \
  --from-literal=branches-exclude=<branches-exclude-value> \
  --from-literal=security-reviewers=<security-reviewers-value> \
  --namespace=<namespace>
```

### AWS

Credentials required to operate your AWS Secret Manager: 
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_SESSION_TOKEN (optional)

```shell
kubectl create secret generic aws-credentials \
  --from-literal=aws-access-key-id=<aws-access-key-id-value> \
  --from-literal=aws-secret-access-key=<aws-secret-access-key-value> \
  --from-literal=aws-session-token=<aws-session-token-value>  # optional \
  --namespace=<namespace>
```

To use with a dedicated IAM role to restrict access:
Associate the IAM role with the K8S service account (e.g., using IRSA for EKS).

### Azure

Credentials required to operate your Azure Key Vault:
- AZURE_CLIENT_ID
- AZURE_CLIENT_SECRET
- AZURE_TENANT_ID (optional)

```shell
kubectl create secret generic azure-credentials \
  --from-literal=azure-client-id=<azure-client-id-value> \
  --from-literal=azure-client-secret=<azure-client-secret-value> \
  --from-literal=azure-tenant-id=<azure-tenant-id-value>  # optional \
  --namespace=<namespace>
```

To use with a dedicated Azure Key Vault role to restrict access:
Associate the Azure Managed Identity with the K8S service account (e.g., using AAD Pod Identity for AKS).

### GCP

- GOOGLE_APPLICATION_CREDENTIALS_JSON
- GOOGLE_CLOUD_PROJECT
- GOOGLE_CLOUD_REGION (optional)
- GOOGLE_API_KEY (optional)

```shell
kubectl create secret generic gcloud-credentials \
  --from-file=google-application-credentials-json=<google-application-credentials-json-file-directory> \
  --from-literal=google-cloud-project=<google-cloud-project-value> \
  # optional
  --from-literal=google-cloud-region=<google-cloud-region-value> \
  --from-literal=google-api-key=<google-api-key-value> \
  --namespace=<namespace>
```

To use with a dedicated GCP role to restrict access:
Associate the GCP IAM role with the K8S service account (e.g., using Workload Identity for GKE).

### Vault

Credentials required to operate Vault, preferably generated with a dedicated AppRole:
- VAULT_ADDR
- VAULT_TOKEN

```shell
kubectl create secret generic vault-approle-credentials \
  --from-literal=vault-addr=<vault-addr-value> \
  --from-literal=vault-token=<vault-token-value> \
  --namespace=<namespace>
```

The best practice is to use Vault Agent with Auto-Auth or Kubernetes Auth to dynamically authenticate and securely retrieve tokens, avoiding static token storage. This is currently unsupported – contributions are welcome.

## Step 2 - Helm deploy

1. Edit [values.yaml](values.yaml).
   * You can configure ingress via the `externalIngress` tree.
2. Run helm upgrade

```shell
helm upgrade -i prevent ./ -n prevent
```

## Step 3 - Create ingress

Depending on platform you're deploying on and the `ingress-controller` you have configured - the ingress yaml
configuration will vary.

Follow the [Kubernetes Ingress docs](https://kubernetes.io/docs/concepts/services-networking/ingress/) and
supported [Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/).