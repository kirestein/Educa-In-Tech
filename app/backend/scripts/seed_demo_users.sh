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

if [[ -n "${PYTHON_BIN:-}" ]]; then
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Erro: PYTHON_BIN definido, mas nao executavel: $PYTHON_BIN" >&2
    exit 1
  fi
else
  if PYTHON_BIN="$(find_python_with_django)"; then
    :
  else
    echo "Erro: nao foi encontrado Python com Django instalado." >&2
    exit 1
  fi
fi

ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin@12345}"
PROF_USERNAME="${PROF_USERNAME:-professor_demo}"
PROF_PASSWORD="${PROF_PASSWORD:-Professor@12345}"
COORD_USERNAME="${COORD_USERNAME:-coordenador_demo}"
COORD_PASSWORD="${COORD_PASSWORD:-Coordenador@12345}"

(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" manage.py shell <<PY
from django.contrib.auth.models import Group, User

specs = [
    {
        "username": "${ADMIN_USERNAME}",
        "password": "${ADMIN_PASSWORD}",
        "is_staff": True,
        "is_superuser": True,
        "groups": [],
    },
    {
        "username": "${PROF_USERNAME}",
        "password": "${PROF_PASSWORD}",
        "is_staff": False,
        "is_superuser": False,
        "groups": ["professor"],
    },
    {
        "username": "${COORD_USERNAME}",
        "password": "${COORD_PASSWORD}",
        "is_staff": False,
        "is_superuser": False,
        "groups": ["coordenador"],
    },
]

for spec in specs:
    user, created = User.objects.get_or_create(username=spec["username"])
    user.is_staff = spec["is_staff"]
    user.is_superuser = spec["is_superuser"]
    user.set_password(spec["password"])
    user.save()

    for group_name in spec["groups"]:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

    status = "criado" if created else "atualizado"
    print(f"Usuario {spec['username']} {status}.")

print("Seed de usuarios demo concluido.")
PY
)
