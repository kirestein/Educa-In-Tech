#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
AUTH_USERNAME="${AUTH_USERNAME:-${LLM_SMOKE_USERNAME:-professor_demo}}"
AUTH_PASSWORD="${AUTH_PASSWORD:-${LLM_SMOKE_PASSWORD:-Professor@12345}}"
TURMA_ID="${TURMA_ID:-1}"
PERGUNTA="${PERGUNTA:-Quais são os principais riscos de desempenho da turma e o que fazer na próxima semana?}"

if ! command -v curl >/dev/null 2>&1; then
  echo "Erro: curl nao encontrado." >&2
  exit 1
fi

echo "1/2 - Obtendo token JWT em $BASE_URL/api/users/token/"
TOKEN_JSON="$(curl -sS -X POST "$BASE_URL/api/users/token/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$AUTH_USERNAME\",\"password\":\"$AUTH_PASSWORD\"}" || true)"

if [[ -z "$TOKEN_JSON" ]]; then
  echo "Falha: API nao respondeu. Verifique se o backend esta rodando em $BASE_URL." >&2
  exit 1
fi

ACCESS_TOKEN="$(python3 - <<'PY' "$TOKEN_JSON"
import json, sys
raw = sys.argv[1]
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    print("")
    sys.exit(0)
print(payload.get("access", ""))
PY
)"

if [[ -z "$ACCESS_TOKEN" ]]; then
  echo "Falha ao obter token. Resposta: $TOKEN_JSON" >&2
  echo "Dica: confirme se o backend esta no ar e se as credenciais AUTH_USERNAME/AUTH_PASSWORD estao corretas." >&2
  exit 1
fi

echo "2/2 - Chamando insights LLM-RAG para turma $TURMA_ID"
RESULT="$(curl -sS -X POST "$BASE_URL/api/integrations/llm-rag/dashboard/turma/$TURMA_ID/insights/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"pergunta\":\"$PERGUNTA\",\"top_k\":6}")"

echo "Resposta:"
echo "$RESULT"

python3 - <<'PY' "$RESULT"
import json
import sys

raw = sys.argv[1]
try:
  payload = json.loads(raw)
except json.JSONDecodeError:
  print("Falha: resposta nao-JSON no endpoint de insights.", file=sys.stderr)
  sys.exit(1)

if isinstance(payload, dict) and payload.get("error"):
  err = payload["error"]
  print(
    f"Falha no smoke test: {err.get('code', 'unknown_error')} - {err.get('message', 'sem mensagem')}",
    file=sys.stderr,
  )
  sys.exit(2)

resultado = payload.get("resultado", {}) if isinstance(payload, dict) else {}
answer = resultado.get("answer") if isinstance(resultado, dict) else None
if not answer:
  print("Falha: resposta sem campo resultado.answer.", file=sys.stderr)
  sys.exit(3)

print("Smoke test LLM-RAG validado com sucesso.")
PY
