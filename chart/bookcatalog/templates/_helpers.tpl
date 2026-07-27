{{/*
Chart name, truncated and trimmed for use in resource names.
*/}}
{{- define "bookcatalog.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Fully qualified app name, e.g. "bookcatalog" or "<release>-bookcatalog".
*/}}
{{- define "bookcatalog.fullname" -}}
{{- if eq .Release.Name .Chart.Name -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Common labels applied to every resource.
*/}}
{{- define "bookcatalog.labels" -}}
app.kubernetes.io/name: {{ include "bookcatalog.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{/*
Selector labels used by Deployments/Services to match Pods.
*/}}
{{- define "bookcatalog.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bookcatalog.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Name of the bundled Postgres resources.
*/}}
{{- define "bookcatalog.postgres.fullname" -}}
{{- printf "%s-postgres" (include "bookcatalog.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
