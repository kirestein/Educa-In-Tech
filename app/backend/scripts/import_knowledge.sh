#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <arquivo_export.json> [--replace]"
  exit 1
fi

INPUT_FILE="$1"
REPLACE=false

for arg in "${@:2}"; do
  case "$arg" in
    --replace) REPLACE=true ;;
    *)
      echo "Opcao invalida: $arg"
      echo "Uso: $0 <arquivo_export.json> [--replace]"
      exit 1
      ;;
  esac
done

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Erro: arquivo nao encontrado: $INPUT_FILE" >&2
  exit 1
fi

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

if [[ "$REPLACE" == true ]]; then
  (
    cd "$BACKEND_DIR"
    "$PYTHON_BIN" manage.py shell <<'PY'
from core.models import KnowledgeChunk, KnowledgeDocument
KnowledgeChunk.objects.all().delete()
KnowledgeDocument.objects.all().delete()
print('Conhecimento existente removido (--replace).')
PY
  )
fi

(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" manage.py loaddata "$INPUT_FILE"
)

echo "Import concluido: $INPUT_FILE"
