#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"
PROJECT_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

find_python_bin() {
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
    if [[ -x "$py" ]]; then
      echo "$py"
      return 0
    fi
  done

  return 1
}

if PYTHON_BIN="$(find_python_bin)"; then
  :
else
  echo "Erro: Python nao encontrado (python/python3)." >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <arquivo_backup> [--force] [--skip-migrate]"
  exit 1
fi

BACKUP_FILE="$1"
FORCE=false
SKIP_MIGRATE=false

for arg in "${@:2}"; do
  case "$arg" in
    --force) FORCE=true ;;
    --skip-migrate) SKIP_MIGRATE=true ;;
    *)
      echo "Opcao invalida: $arg"
      echo "Uso: $0 <arquivo_backup> [--force] [--skip-migrate]"
      exit 1
      ;;
  esac
done

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Erro: arquivo de backup nao encontrado: $BACKUP_FILE" >&2
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ "$BACKUP_FILE" == *.dump ]]; then
  if [[ "${DATABASE_URL:-}" != postgresql://* && "${DATABASE_URL:-}" != postgres://* ]]; then
    echo "Erro: DATABASE_URL PostgreSQL nao configurada para restore de .dump" >&2
    exit 1
  fi

  if ! command -v pg_restore >/dev/null 2>&1; then
    echo "Erro: pg_restore nao encontrado. Instale o cliente PostgreSQL." >&2
    exit 1
  fi

  if [[ "$FORCE" != true ]]; then
    echo "Restore PostgreSQL vai sobrescrever objetos no banco configurado em DATABASE_URL."
    read -r -p "Digite RESTORE para confirmar: " confirm
    if [[ "$confirm" != "RESTORE" ]]; then
      echo "Operacao cancelada."
      exit 1
    fi
  fi

  pg_restore --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" "$BACKUP_FILE"

  if [[ "$SKIP_MIGRATE" != true ]]; then
    (cd "$BACKEND_DIR" && "$PYTHON_BIN" manage.py migrate)
  fi

  echo "Restore PostgreSQL concluido."
  exit 0
fi

TARGET_SQLITE="${SQLITE_FILE:-$BACKEND_DIR/db.sqlite3}"

if [[ "$FORCE" != true ]]; then
  echo "Restore SQLite vai substituir: $TARGET_SQLITE"
  read -r -p "Digite RESTORE para confirmar: " confirm
  if [[ "$confirm" != "RESTORE" ]]; then
    echo "Operacao cancelada."
    exit 1
  fi
fi

cp "$BACKUP_FILE" "$TARGET_SQLITE"

if [[ "$SKIP_MIGRATE" != true ]]; then
  (cd "$BACKEND_DIR" && "$PYTHON_BIN" manage.py migrate)
fi

echo "Restore SQLite concluido."
