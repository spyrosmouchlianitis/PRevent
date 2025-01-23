# PRevent Helm Chart

## Step 1 - prerequisites

Create a namespace for the prevent helm chart

```shell
kubectl create namespace <namespace>
```

Create a Kubernetes secret for your secret manager credentials
Choose one of the following:

#### Vault

```shell
kubectl create secret generic vault-credentials \
  --from-literal=vault-addr=<vault-addr-value> \
  --from-literal=vault-token=<vault-token-value> \
  --namespace=<namespace>
```

#### AWS

```shell
kubectl create secret generic aws-credentials \
  --from-literal=aws-access-key-id=<aws-access-key-id-value> \
  --from-literal=aws-secret-access-key=<aws-secret-access-key-value> \
  # optional
  --from-literal=aws-session-token=<aws-session-token-value> \
  --namespace=<namespace>
```

#### Azure

```shell
kubectl create secret generic azure-credentials \
  --from-literal=azure-client-id=<azure-client-id-value> \
  --from-literal=azure-client-secret=<azure-client-secret-value> \
  # optional
  --from-literal=azure-tenant-id=<azure-tenant-id-value> \
  --namespace=<namespace>
```

#### GCP

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
2. Run helm upgrade

```shell
helm upgrade -i prevent ./ -n prevent
```