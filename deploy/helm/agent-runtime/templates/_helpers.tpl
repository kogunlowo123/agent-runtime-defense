{{- define "agent-runtime.fullname" -}}
{{- printf "%s-%s" .Release.Name "agent-runtime" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "agent-runtime.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{ include "agent-runtime.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "agent-runtime.selectorLabels" -}}
app.kubernetes.io/name: agent-runtime
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
