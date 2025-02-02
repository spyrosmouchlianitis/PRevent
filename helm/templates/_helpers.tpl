{{- define "secret-set-key-ref" }}
  - name: {{ .env }}
    valueFrom:
      secretKeyRef:
        name: {{ .name }}
        key: {{ .key }}
{{- end }}

{{- define "secret-check-key" }}
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

{{- define "set-env-secrets" }}

{{- end }}