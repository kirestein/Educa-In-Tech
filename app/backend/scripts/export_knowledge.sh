#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"
OUTPUT_FILE="${1:-$BACKEND_DIR/backups/knowledge_export_$(date +%Y%m%d_%H%M%S).json}"

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

if ! PYTHON_BIN="$(find_python_with_django)"; then
  echo "Erro: nao foi encontrado Python com Django instalado." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"

(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" manage.py dumpdata core.KnowledgeDocument core.KnowledgeChunk --indent 2 >"$OUTPUT_FILE"
)

echo "Export concluido: $OUTPUT_FILE"
