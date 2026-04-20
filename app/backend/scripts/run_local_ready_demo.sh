#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"
APP_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8012}"
BASE_URL="http://$HOST:$PORT"
WAIT_SECONDS="${WAIT_SECONDS:-45}"
RUN_LLM_INSIGHTS="${RUN_LLM_INSIGHTS:-false}"
LOCAL_LLM_MODEL="${LOCAL_LLM_MODEL:-qwen2.5:0.5b}"

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
  local max_tries=30
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

if [[ ! -f "$ENV_FILE" ]]; then
  "$SCRIPT_DIR/init_local_env.sh"
fi

if [[ "$RUN_LLM_INSIGHTS" == "true" ]]; then
  echo "Preparando modelo LLM local para teste de insights..."
  LOCAL_LLM_MODEL="$LOCAL_LLM_MODEL" "$SCRIPT_DIR/ensure_local_llm_model.sh" "$LOCAL_LLM_MODEL"
fi

export LOCAL_LLM_MODEL

if port_in_use "$PORT"; then
  echo "Porta $PORT em uso. Procurando porta livre..."
  if NEW_PORT="$(find_available_port "$((PORT + 1))")"; then
    PORT="$NEW_PORT"
    BASE_URL="http://$HOST:$PORT"
    echo "Usando porta alternativa: $PORT"
  else
    echo "Erro: nao foi possivel encontrar porta livre para a demo local." >&2
    exit 1
  fi
fi

SERVER_PID=""
cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "[1/7] Check e migrations"
(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" manage.py check
  "$PYTHON_BIN" manage.py migrate --noinput
)

echo "[2/7] Seed de usuarios demo"
PYTHON_BIN="$PYTHON_BIN" "$SCRIPT_DIR/seed_demo_users.sh"

echo "[3/7] Seed de dados acadêmicos mínimos"
TURMA_ID_RAW="$(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" manage.py shell <<'PY'
from datetime import date
from core.models import Disciplina, Unidade, Turma, Aluno, Avaliacao, Nota

mat, _ = Disciplina.objects.get_or_create(nome='Matematica Aplicada', defaults={'codigo': 'MAT-APL'})
uni, _ = Unidade.objects.get_or_create(nome='Maple Bear Santana', cidade='Sao Paulo', estado='SP')
turma, _ = Turma.objects.get_or_create(nome='Year 6A', ano_letivo=2026, disciplina=mat, unidade=uni)

if not Aluno.objects.filter(turma=turma).exists():
    a1 = Aluno.objects.create(nome='Ana Lima', matricula='2026-Y6A-001', turma=turma)
    a2 = Aluno.objects.create(nome='Bruno Reis', matricula='2026-Y6A-002', turma=turma)
    av = Avaliacao.objects.create(
        titulo='Avaliacao Diagnostica 1',
        tipo='formativa',
        turma=turma,
        peso=1,
        data_aplicacao=date(2026, 3, 10),
    )
    Nota.objects.create(aluno=a1, avaliacao=av, valor=8.5)
    Nota.objects.create(aluno=a2, avaliacao=av, valor=6.5)

print(turma.id)
PY
)"

TURMA_ID="$(printf '%s\n' "$TURMA_ID_RAW" | tail -n 1 | tr -d '[:space:]')"
if [[ -z "$TURMA_ID" ]]; then
  echo "Erro: nao foi possivel determinar TURMA_ID de demo." >&2
  exit 1
fi

echo "Turma de demo: $TURMA_ID"

echo "[4/7] Subindo API local em $BASE_URL"
(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" manage.py runserver "$HOST:$PORT" >"$BACKEND_DIR/test-output.log" 2>&1
) &
SERVER_PID=$!

echo "[5/7] Aguardando healthcheck"
READY=false
for _ in $(seq 1 "$WAIT_SECONDS"); do
  if curl -fsS "$BASE_URL/api/health/" >/dev/null 2>&1; then
    READY=true
    break
  fi
  sleep 1
done

if [[ "$READY" != "true" ]]; then
  echo "Falha: API nao ficou pronta em ${WAIT_SECONDS}s" >&2
  tail -n 40 "$BACKEND_DIR/test-output.log" >&2 || true
  exit 1
fi

TOKEN="$(curl -sS -X POST "$BASE_URL/api/users/token/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@12345"}' | "$PYTHON_BIN" -c "import sys,json; print(json.load(sys.stdin)['access'])")"

echo "[6/7] Ingerindo conhecimento manual de exemplo"
curl -sS -X POST "$BASE_URL/api/knowledge/documents/ingest-text/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id":"manual:plano-recuperacao:2026-03",
    "source_type":"manual",
    "title":"Plano de recuperação de aprendizagem",
    "turma_id":'"$TURMA_ID"',
    "text":"Implementar reforço semanal para alunos com média abaixo de 7.\n\nAplicar avaliação curta toda sexta-feira para medir evolução.\n\nRegistrar feedback individual e plano de estudo em cada ciclo."
  }' | cat

echo

echo "[7/7] Buscando conhecimento no acervo"
curl -sS "$BASE_URL/api/knowledge/chunks/search/?q=reforco%20semanal&limit=5&turma_id=$TURMA_ID" \
  -H "Authorization: Bearer $TOKEN" | cat

echo
if [[ "$RUN_LLM_INSIGHTS" == "true" ]]; then
  echo "Executando insights LLM (opcional)..."
  curl -sS -X POST "$BASE_URL/api/integrations/llm-rag/dashboard/turma/$TURMA_ID/insights/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"pergunta":"Quais ações priorizar para elevar a média?","top_k":6}' | cat
  echo
fi

echo "Sistema pronto e validado localmente."
echo "Base URL: $BASE_URL"
echo "Usuario admin para testes: admin / Admin@12345"
