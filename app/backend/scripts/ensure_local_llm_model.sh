#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-${LOCAL_LLM_MODEL:-qwen2.5:0.5b}}"
BASE_URL="${LOCAL_LLM_BASE_URL:-http://127.0.0.1:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Erro: ollama nao encontrado no PATH." >&2
  exit 1
fi

if ! curl -fsS "$BASE_URL/api/tags" >/dev/null 2>&1; then
  echo "Erro: Ollama nao esta acessivel em $BASE_URL." >&2
  exit 1
fi

if ollama list | awk 'NR>1 {print $1}' | grep -Fx "$MODEL" >/dev/null 2>&1; then
  echo "Modelo ja disponivel: $MODEL"
else
  echo "Baixando modelo leve para ambiente local: $MODEL"
  ollama pull "$MODEL"
fi

TEST_RESPONSE="$(curl -sS -X POST "$BASE_URL/api/generate" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"$MODEL\",\"prompt\":\"Responda apenas: ok\",\"stream\":false,\"options\":{\"temperature\":0.0}}" || true)"

if printf '%s' "$TEST_RESPONSE" | grep -q '"error"'; then
  echo "Falha no teste do modelo $MODEL: $TEST_RESPONSE" >&2
  exit 1
fi

echo "Modelo validado com sucesso: $MODEL"
