{{- define "secret-keyref-required" }}
  - name: {{ .env }}
    valueFrom:
      secretKeyRef:
        name: {{ .name }}
        key: {{ .key }}
{{- end }}

{{- define "secret-keyref-optional" }}
  {{- $secret := (lookup "v1" "Secret" .namespace .name) -}}
  {{- $value := (index $secret.data .key) -}}
  {{- if $value }}
  - name: {{ .env }}
    valueFrom:
      secretKeyRef:
        name: {{ .name }}
        key: {{ .key }}
  {{- end }}
{{- end }}

{{- define "env-secrets" }}
  {{- if eq .secreteManagerType "vault" }}
    {{- include "secret-keyref-required" (dict "name" "vault-credentials" "key" "vault-addr" "env" "VAULT_ADDR") }}
    {{- include "secret-keyref-required" (dict "name" "vault-credentials" "key" "vault-token" "env" "VAULT_TOKEN") }}
  {{- end }}
  {{- if eq .secreteManagerType "aws" }}
    {{- include "secret-keyref-required" (dict "name" "aws-credentials" "key" "aws-access-key-id" "env" "AWS_ACCESS_KEY_ID") }}
    {{- include "secret-keyref-required" (dict "name" "aws-credentials" "key" "aws-secret-access-key" "env" "AWS_SECRET_ACCESS_KEY") }}
    {{- include "secret-keyref-optional" (dict "name" "aws-credentials" "key" "aws-session-token" "env" "AWS_SESSION_TOKEN" "namespace" .Release.Namespace) }}
  {{- end }}
  {{- if eq .secreteManagerType "azure" }}
    {{- include "secret-keyref-required" (dict "name" "azure-credentials" "key" "azure-client-id" "env" "AZURE_CLIENT_ID") }}
    {{- include "secret-keyref-required" (dict "name" "azure-credentials" "key" "azure-client-secret" "env" "AZURE_CLIENT_SECRET") }}
    {{- include "secret-keyref-optional" (dict "name" "azure-credentials" "key" "azure-tenant-id" "env" "AZURE_TENANT_ID" "namespace" .Release.Namespace) }}
  {{- end }}
  {{- if eq .secreteManagerType "gcloud" }}
    {{- include "secret-keyref-required" (dict "name" "gcloud-credentials" "key" "google-cloud-project" "env" "GOOGLE_CLOUD_PROJECT") }}
    {{- include "secret-keyref-optional" (dict "name" "gcloud-credentials" "key" "google-cloud-region" "env" "GOOGLE_CLOUD_REGION" "namespace" .Release.Namespace) }}
    {{- include "secret-keyref-optional" (dict "name" "gcloud-credentials" "key" "google-api-key" "env" "GOOGLE_API_KEY" "namespace" .Release.Namespace) }}
  {{- end }}
  {{- if eq .secreteManagerType "k8s" }}
    {{- include "secret-keyref-required" (dict "name" "k8s-credentials" "key" "github-app-private-key" "env" "GITHUB_APP_PRIVATE_KEY") }}
    {{- include "secret-keyref-required" (dict "name" "k8s-credentials" "key" "github-app-integration-id" "env" "GITHUB_APP_INTEGRATION_ID") }}
    {{- include "secret-keyref-required" (dict "name" "k8s-credentials" "key" "webhook-secret" "env" "WEBHOOK_SECRET") }}
    {{- include "secret-keyref-optional" (dict "name" "k8s-credentials" "key" "branches-include" "env" "BRANCHES_INCLUDE" "namespace" .Release.Namespace) }}
    {{- include "secret-keyref-optional" (dict "name" "k8s-credentials" "key" "branches-exclude" "env" "BRANCHES_EXCLUDE" "namespace" .Release.Namespace) }}
    {{- include "secret-keyref-optional" (dict "name" "k8s-credentials" "key" "security-reviewers" "env" "SECURITY_REVIEWERS" "namespace" .Release.Namespace) }}
  {{- end }}
{{- end }}
