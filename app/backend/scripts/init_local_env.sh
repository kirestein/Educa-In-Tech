#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"
FORCE="${FORCE:-false}"

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    *)
      echo "Opcao invalida: $arg"
      echo "Uso: $0 [--force]"
      exit 1
      ;;
  esac
done

if [[ -f "$ENV_FILE" && "$FORCE" != "true" ]]; then
  echo "Arquivo .env ja existe em $ENV_FILE. Use --force para sobrescrever."
  exit 0
fi

cat >"$ENV_FILE" <<'EOF'
# Django local
SECRET_KEY=dev-secret-key-change-me-please-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_SIGNING_KEY=dev-jwt-signing-key-change-me-please-change-this-32chars
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=1

# Database local (fallback sqlite)
DB_CONN_MAX_AGE=600

# Google Sheets (opcional)
GOOGLE_SHEETS_CREDENTIALS_FILE=
GOOGLE_SHEETS_DEFAULT_SPREADSHEET_ID=
GOOGLE_SHEETS_DEFAULT_WORKSHEET=dashboard_turmas

# LLM local + RAG
LOCAL_LLM_ENABLED=True
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=qwen2.5:0.5b
LOCAL_LLM_FALLBACK_MODEL=qwen2.5:0.5b
LOCAL_LLM_API_KEY=
LOCAL_LLM_AUTH_HEADER=Authorization
LOCAL_LLM_USE_BEARER=True
LOCAL_LLM_RETRY_ATTEMPTS=2
LOCAL_LLM_RETRY_BACKOFF_SECONDS=1.0
LOCAL_LLM_CIRCUIT_FAILURE_THRESHOLD=3
LOCAL_LLM_CIRCUIT_OPEN_SECONDS=30
LOCAL_LLM_TIMEOUT_SECONDS=60
LOCAL_LLM_TEMPERATURE=0.2
LOCAL_LLM_MAX_CONTEXT_DOCS=8
EOF

echo "Arquivo .env local criado em: $ENV_FILE"
