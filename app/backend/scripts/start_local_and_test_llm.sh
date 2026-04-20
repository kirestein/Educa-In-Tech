#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

find_python_with_django() {
  local candidates=()
  candidates+=("$PROJECT_ROOT/.venv/bin/python")
  candidates+=("$PROJECT_ROOT/app/.venv/bin/python")

  if command -v python >/dev/null 2>&1; then
    candidates+=("$(command -v python)")
  fi
  if command -v python3 >/dev/null 2>&1; then
    candidates+=("$(command -v python3)")
  fi

  local py
  for py in "${candidates[@]}"; do
    if [[ -x "$py" ]] && "$py" -c "import django" >/dev/null 2>&1; then
      echo "$py"
      return 0
    fi
  done

  return 1
}

if PYTHON_BIN="$(find_python_with_django)"; then
  :
else
  echo "Erro: nao foi encontrado Python com Django instalado." >&2
  echo "Dica: ative a virtualenv do projeto ou instale dependencias em app/requirements.txt." >&2
  exit 1
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BASE_URL="${BASE_URL:-http://$HOST:$PORT}"
WAIT_SECONDS="${WAIT_SECONDS:-45}"
START_SERVER="${START_SERVER:-true}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
SEED_DEMO_USERS="${SEED_DEMO_USERS:-true}"
AUTO_INIT_ENV="${AUTO_INIT_ENV:-true}"
LOG_FILE="${LOG_FILE:-$BACKEND_DIR/test-output.log}"
APP_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"

SERVER_PID=""

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$port" | tail -n +2 | grep -q ":$port"
    return $?
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

find_available_port() {
  local start_port="$1"
  local max_tries=20
  local current_port="$start_port"
  local i

  for i in $(seq 1 "$max_tries"); do
    if ! port_in_use "$current_port"; then
      echo "$current_port"
      return 0
    fi
    current_port=$((current_port + 1))
  done

  return 1
}

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}

if [[ "$START_SERVER" == "true" ]]; then
  trap cleanup EXIT INT TERM

  if [[ ! -f "$ENV_FILE" && "$AUTO_INIT_ENV" == "true" ]]; then
    echo "Arquivo .env nao encontrado. Inicializando ambiente local..."
    "$SCRIPT_DIR/init_local_env.sh"
  fi

  if port_in_use "$PORT"; then
    echo "Porta $PORT em uso. Procurando porta livre..."
    if NEW_PORT="$(find_available_port "$((PORT + 1))")"; then
      PORT="$NEW_PORT"
      BASE_URL="http://$HOST:$PORT"
      echo "Usando porta alternativa: $PORT"
    else
      echo "Erro: nao foi possivel encontrar porta livre para subir o servidor." >&2
      exit 1
    fi
  fi

  echo "[1/4] Validando configuracao Django"
  (cd "$BACKEND_DIR" && "$PYTHON_BIN" manage.py check)

  if [[ "$RUN_MIGRATIONS" == "true" ]]; then
    echo "[2/4] Aplicando migrations"
    (cd "$BACKEND_DIR" && "$PYTHON_BIN" manage.py migrate --noinput)
  else
    echo "[2/4] Migrations puladas (RUN_MIGRATIONS=false)"
  fi

  if [[ "$SEED_DEMO_USERS" == "true" ]]; then
    echo "[2.1/4] Garantindo usuarios demo para smoke test"
    PYTHON_BIN="$PYTHON_BIN" "$SCRIPT_DIR/seed_demo_users.sh"
  fi

  echo "[3/4] Subindo servidor Django em $HOST:$PORT"
  (cd "$BACKEND_DIR" && "$PYTHON_BIN" manage.py runserver "$HOST:$PORT" >"$LOG_FILE" 2>&1) &
  SERVER_PID=$!
else
  echo "[1/4] START_SERVER=false, assumindo servidor ja em execucao em $BASE_URL"
fi

echo "[4/4] Aguardando healthcheck em $BASE_URL/api/health/"
READY=false
for _ in $(seq 1 "$WAIT_SECONDS"); do
  if curl -fsS "$BASE_URL/api/health/" >/dev/null 2>&1; then
    READY=true
    break
  fi
  sleep 1
done

if [[ "$READY" != "true" ]]; then
  echo "Falha: API nao ficou pronta em ${WAIT_SECONDS}s." >&2
  if [[ -f "$LOG_FILE" ]]; then
    echo "Ultimas linhas do log ($LOG_FILE):" >&2
    tail -n 40 "$LOG_FILE" >&2 || true
  fi
  exit 1
fi

echo "API pronta. Executando smoke test LLM-RAG..."
BASE_URL="$BASE_URL" "$SCRIPT_DIR/smoke_test_llm.sh"

echo "Fluxo concluido com sucesso."
