#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"
BACKUP_DIR="${BACKUP_DIR:-$BACKEND_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

mkdir -p "$BACKUP_DIR"

sha256_file() {
  local file_path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file_path" >"${file_path}.sha256"
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file_path" >"${file_path}.sha256"
  fi
}

if [[ "${DATABASE_URL:-}" == postgresql://* || "${DATABASE_URL:-}" == postgres://* ]]; then
  if ! command -v pg_dump >/dev/null 2>&1; then
    echo "Erro: pg_dump nao encontrado. Instale o cliente PostgreSQL." >&2
    exit 1
  fi

  OUTPUT_FILE="$BACKUP_DIR/postgres_${TIMESTAMP}.dump"
  pg_dump "$DATABASE_URL" -Fc -f "$OUTPUT_FILE"
  sha256_file "$OUTPUT_FILE"
  echo "Backup PostgreSQL criado em: $OUTPUT_FILE"
  exit 0
fi

SQLITE_FILE="${SQLITE_FILE:-$BACKEND_DIR/db.sqlite3}"
if [[ ! -f "$SQLITE_FILE" ]]; then
  echo "Erro: SQLite nao encontrado em $SQLITE_FILE" >&2
  exit 1
fi

OUTPUT_FILE="$BACKUP_DIR/sqlite_${TIMESTAMP}.sqlite3"
cp "$SQLITE_FILE" "$OUTPUT_FILE"
sha256_file "$OUTPUT_FILE"

echo "Backup SQLite criado em: $OUTPUT_FILE"
