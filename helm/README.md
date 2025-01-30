# PRevent Helm Chart

Credentials required to operate your secret manager's dedicated app-role:

| Vault       | AWS                          | Azure                      | GCloud                              |
|-------------|------------------------------|----------------------------|-------------------------------------|
| VAULT_ADDR  | AWS_ACCESS_KEY_ID            | AZURE_CLIENT_ID            | GOOGLE_APPLICATION_CREDENTIALS_JSON | 
| VAULT_TOKEN | AWS_SECRET_ACCESS_KEY        | AZURE_CLIENT_SECRET        | GOOGLE_CLOUD_PROJECT                |
|             | AWS_SESSION_TOKEN (optional) | AZURE_TENANT_ID (optional) | GOOGLE_CLOUD_REGION (optional)      |
|             |                              |                            | GOOGLE_API_KEY (optional)           |

## Step 1 - prerequisites

Create a namespace for the PRevent helm chart

```shell
kubectl create namespace <namespace>
```

Create a Kubernetes secret for your secret manager credentials
Choose one of the following:

### Vault

```shell
kubectl create secret generic vault-credentials \
  --from-literal=vault-addr=<vault-addr-value> \
  --from-literal=vault-token=<vault-token-value> \
  --namespace=<namespace>
```

### AWS

```shell
kubectl create secret generic aws-credentials \
  --from-literal=aws-access-key-id=<aws-access-key-id-value> \
  --from-literal=aws-secret-access-key=<aws-secret-access-key-value> \
  # optional
  --from-literal=aws-session-token=<aws-session-token-value> \
  --namespace=<namespace>
```

### Azure

```shell
kubectl create secret generic azure-credentials \
  --from-literal=azure-client-id=<azure-client-id-value> \
  --from-literal=azure-client-secret=<azure-client-secret-value> \
  # optional
  --from-literal=azure-tenant-id=<azure-tenant-id-value> \
  --namespace=<namespace>
```

### GCP

```shell
kubectl create secret generic gcloud-credentials \
  --from-file=google-application-credentials-json=<google-application-credentials-json-file-directory> \
  --from-literal=google-cloud-project=<google-cloud-project-value> \
  # optional
  --from-literal=google-cloud-region=<google-cloud-region-value> \
  --from-literal=google-api-key=<google-api-key-value> \
  --namespace=<namespace>
```

## Step 2 - Helm deploy

1. Edit [values.yaml](values.yaml)
    1. If you're deploying on GKE you can configure ingress also via the `externalIngress` tree.
2. Run helm upgrade

```shell
helm upgrade -i prevent ./ -n prevent
```

## Step 3 - Create ingress

Depending on platform you're deploying on and the `ingress-controller` you have configured - the ingress yaml
configuration will vary.

Follow the [Kubernetes Ingress docs](https://kubernetes.io/docs/concepts/services-networking/ingress/) and
supported [Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/).