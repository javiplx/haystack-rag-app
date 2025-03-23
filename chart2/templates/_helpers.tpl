{{- define "prefix" -}}
{{- if .Values.prefix.enabled }}haystack-{{ end -}}
{{- end }}
