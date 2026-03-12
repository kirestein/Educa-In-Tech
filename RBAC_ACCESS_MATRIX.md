# Matriz de Acesso RBAC — Educa in Tech

Data de referência: 12 de março de 2026

## 1) Perfis considerados

- **Anônimo**: sem token JWT.
- **Autenticado (sem grupo)**: usuário logado sem `professor`/`coordenador`.
- **Professor**: usuário no grupo `professor`.
- **Coordenador**: usuário no grupo `coordenador`.
- **Admin**: `is_staff=True` (inclui superuser).

## 2) Regras globais

- Endpoints do `core` exigem autenticação por padrão.
- Nos `ModelViewSet` do `core`:
  - `list`/`retrieve`: **qualquer usuário autenticado**.
  - escrita (`create`, `update`, `partial_update`, `destroy`): depende do recurso.
- Endpoint de dashboard da turma exige **professor ou nível superior**.
- Atribuição de role em `users` exige **admin**.

## 3) Matriz por endpoint

| Endpoint                                       | Método                | Anônimo | Autenticado | Professor | Coordenador | Admin |
| ---------------------------------------------- | --------------------- | ------: | ----------: | --------: | ----------: | ----: |
| `/api/health/`                                 | GET                   |      ✅ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/users/health/`                           | GET                   |      ✅ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/users/token/`                            | POST                  |      ✅ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/users/token/refresh/`                    | POST                  |      ✅ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/users/me/`                               | GET                   |      ❌ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/users/roles/assign/`                     | POST                  |      ❌ |          ❌ |        ❌ |          ❌ |    ✅ |
| `/api/dashboard/turma/{id}/`                   | GET                   |      ❌ |          ❌ |        ✅ |          ✅ |    ✅ |
| `/api/disciplinas/` e `/api/disciplinas/{id}/` | GET                   |      ❌ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/disciplinas/` e `/api/disciplinas/{id}/` | POST/PUT/PATCH/DELETE |      ❌ |          ❌ |        ❌ |          ✅ |    ✅ |
| `/api/unidades/` e `/api/unidades/{id}/`       | GET                   |      ❌ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/unidades/` e `/api/unidades/{id}/`       | POST/PUT/PATCH/DELETE |      ❌ |          ❌ |        ❌ |          ✅ |    ✅ |
| `/api/turmas/` e `/api/turmas/{id}/`           | GET                   |      ❌ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/turmas/` e `/api/turmas/{id}/`           | POST/PUT/PATCH/DELETE |      ❌ |          ❌ |        ❌ |          ✅ |    ✅ |
| `/api/turmas/{id}/transferir_aluno/`           | POST                  |      ❌ |          ❌ |        ❌ |          ✅ |    ✅ |
| `/api/alunos/` e `/api/alunos/{id}/`           | GET                   |      ❌ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/alunos/` e `/api/alunos/{id}/`           | POST/PUT/PATCH/DELETE |      ❌ |          ❌ |        ❌ |          ✅ |    ✅ |
| `/api/avaliacoes/` e `/api/avaliacoes/{id}/`   | GET                   |      ❌ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/avaliacoes/` e `/api/avaliacoes/{id}/`   | POST/PUT/PATCH/DELETE |      ❌ |          ❌ |        ✅ |          ✅ |    ✅ |
| `/api/notas/` e `/api/notas/{id}/`             | GET                   |      ❌ |          ✅ |        ✅ |          ✅ |    ✅ |
| `/api/notas/` e `/api/notas/{id}/`             | POST/PUT/PATCH/DELETE |      ❌ |          ❌ |        ✅ |          ✅ |    ✅ |

## 4) Fontes de verdade (código)

- Permissões customizadas: `app/backend/core/permissions.py`
- Regras por ação dos recursos do core: `app/backend/core/views.py`
- Rotas do core: `app/backend/core/urls.py`
- Rotas de usuários: `app/backend/users/urls.py`
- Permissões de usuários: `app/backend/users/views.py`

## 5) Observações

- `IsAdminUser` no endpoint `/api/users/roles/assign/` depende de `is_staff=True`.
- Superuser normalmente também é `is_staff=True`.
- Em caso de evolução de regra por endpoint, esta matriz deve ser atualizada junto do código e dos testes de autorização.
