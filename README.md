# Educa in Tech — README

Este documento registra, de forma objetiva, tudo o que foi implementado até o momento no projeto.

## 0) Política de atualização deste README

A partir desta etapa, este arquivo será atualizado a cada entrega incremental (nova feature, ajuste técnico, correção ou refatoração relevante), contendo:
- o que foi alterado;
- em quais arquivos;
- como validar;
- status do check técnico.

## 0.1) Git & Commits

**Convenção de branches:** `feat/`, `fix/`, `docs/`, `chore/` (ex: `feat/backend-bootstrap-academic-api`)

**Convenção de commits:** Type(scope): mensagem breve
- `feat`: nova feature
- `fix`: correção de bug
- `docs`: documentação
- `ci`: pipeline/automação

**Pipeline CI/CD:**
- GitHub Actions automaticamente valida cada push
- Arquivo: `.github/workflows/backend-checks.yml`
- Checagens: `manage.py check`, migrations validation, testes, code style hints

**Status atual:**
- Branch: `feat/backend-bootstrap-academic-api`
- Commits: 2
  - `7e71de0` feat(backend): bootstrap academic API and JWT auth base
  - `2afd214` ci: add GitHub Actions pipeline for backend checks
- Remoto: `origin` (git@github.com:kirestein/Educa-In-Tech.git)

## 1) Contexto do que foi feito

Foi iniciada a estrutura funcional do backend Django para o domínio acadêmico, saindo de uma base quase vazia para uma API REST com modelos, rotas, serializers, admin e migração inicial.

## 2) Implementações concluídas

### 2.1 Modelagem de domínio (Django ORM)

Arquivo principal: `app/backend/core/models.py`

Modelos criados:
- `Disciplina`
- `Unidade`
- `Turma`
- `Aluno`
- `Avaliacao`
- `Nota`

Principais regras aplicadas:
- Chaves estrangeiras entre entidades acadêmicas (`Turma -> Disciplina/Unidade`, `Aluno -> Turma`, `Avaliacao -> Turma`, `Nota -> Aluno/Avaliacao`).
- Restrições de unicidade para evitar duplicidade de contexto:
  - unidade por combinação de localização;
  - turma por combinação nome/ano/disciplina/unidade;
  - nota única por aluno + avaliação.
- Campos de apoio para avaliação:
  - tipo (mensal/trimestral/formativa/oral), peso, prazo, penalidade.

### 2.2 API REST (Django REST Framework)

Arquivos:
- `app/backend/core/serializers.py`
- `app/backend/core/views.py`
- `app/backend/core/urls.py`

Implementado:
- Serializers para todos os modelos de `core`.
- ViewSets com CRUD para:
  - disciplinas
  - unidades
  - turmas
  - alunos
  - avaliações
  - notas
- Endpoint customizado para transferência de aluno entre turmas.
- Endpoint de dashboard resumido por turma com:
  - média geral
  - total de alunos
  - total de avaliações
- Endpoint de healthcheck do módulo core.

### 2.3 Rotas e organização de URLs

Arquivo alterado:
- `app/backend/config/urls.py`

Ajustes:
- Inclusão de `core.urls` na base `/api/`.
- Inclusão de `users.urls` na base `/api/users/`.

### 2.4 Módulo users mínimo para não quebrar include

Arquivos:
- `app/backend/users/views.py`
- `app/backend/users/urls.py`

Implementado:
- Healthcheck simples para `users`.
- Endpoint JWT de login (`/api/users/token/`) e refresh (`/api/users/token/refresh/`).
- Endpoint de perfil autenticado (`/api/users/me/`).
- Endpoint de atribuição de perfil (`/api/users/roles/assign/`) para admin.

Ajuste adicional:
- Limpeza de import não utilizado em `app/backend/users/models.py`.

### 2.5 Admin Django

Arquivo alterado:
- `app/backend/core/admin.py`

Implementado:
- Registro de todos os modelos de `core` no Django Admin.
- Configuração de `list_display`, `search_fields` e `list_filter` para facilitar operação.

### 2.6 Migrações

Arquivo gerado:
- `app/backend/core/migrations/0001_initial.py`

Status:
- Migração inicial criada com os modelos e constraints do domínio.

### 2.7 Verificação técnica

Comandos executados:
- `manage.py check`
- `manage.py makemigrations core`
- `manage.py check` (novamente)

Resultado:
- `System check identified no issues (0 silenced).`

## 3) Endpoints disponíveis até agora

Base principal: `/api/`

Recursos REST:
- `/api/disciplinas/`
- `/api/unidades/`
- `/api/turmas/`
- `/api/alunos/`
- `/api/avaliacoes/`
- `/api/notas/`

Endpoints adicionais:
- `/api/health/`
- `/api/dashboard/turma/<id>/`
- `/api/turmas/<id>/transferir_aluno/` (POST)
- `/api/users/health/`
- `/api/users/token/` (POST)
- `/api/users/token/refresh/` (POST)
- `/api/users/me/` (GET)
- `/api/users/roles/assign/` (POST, admin)

## 4) O que ainda não foi implementado

Itens planejados, mas ainda pendentes:
- Testes automatizados de API e domínio.
- Dashboards avançados com séries e dispersão.
- Integração com Google Sheets.
- Integração backend ↔ microserviço de IA.
- Documentação de API (OpenAPI/Swagger) e padronização de erros.

## 5) Próximo passo sugerido

Implementar testes automatizados para autenticação, autorização por perfil e fluxos de negócio principais da API.

## 6) Como testar o que já foi implementado

### 6.1 Preparar ambiente

1. Ative o ambiente virtual na raiz do projeto (`Educa_in_tech`).
2. Instale dependências em `app/requirements.txt`.
3. Entre em `app/backend`.
4. Rode migrações.
5. Inicie o servidor Django.

Sequência de referência:

```bash
cd /home/kirestein/Documentos/projects/Educa_in_tech
source .venv/bin/activate
pip install -r app/requirements.txt
cd app/backend
python manage.py migrate
python manage.py runserver
```

### 6.2 Verificar healthchecks

No navegador ou via `curl`:

- `GET http://127.0.0.1:8000/api/health/`
- `GET http://127.0.0.1:8000/api/users/health/`

Se estiver tudo certo, ambos retornam `status: ok`.

### 6.3 Autenticação JWT (obrigatória para API)

Atualmente, os endpoints de `core` exigem token Bearer.

#### Credenciais de teste já criadas

- admin
  - username: `admin`
  - password: `Admin@12345`
- professor
  - username: `professor_demo`
  - password: `Professor@12345`
- coordenador
  - username: `coordenador_demo`
  - password: `Coordenador@12345`

#### Obter token

```bash
curl -X POST http://127.0.0.1:8000/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"professor_demo","password":"Professor@12345"}'
```

Use o `access` retornado no header:

```bash
Authorization: Bearer <ACCESS_TOKEN>
```

#### Conferir usuário logado

```bash
curl http://127.0.0.1:8000/api/users/me/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 6.4 Teste funcional completo (ordem recomendada)

#### 1) Criar disciplina

> Importante: **não envie `id` no payload**. O `id` é gerado automaticamente pelo banco.

```bash
curl -X POST http://127.0.0.1:8000/api/disciplinas/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Matemática","codigo":"MAT-01"}'
```

Guarde o `id` retornado como `disciplina_id`.

Exemplo de resposta esperada (resumo):

```json
{
  "id": 1,
  "nome": "Matemática",
  "codigo": "MAT-01"
}
```

#### 2) Criar unidade

```bash
curl -X POST http://127.0.0.1:8000/api/unidades/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Escola Central","cidade":"São Paulo","estado":"SP"}'
```

Guarde o `id` retornado como `unidade_id`.

#### 3) Criar turma

```bash
curl -X POST http://127.0.0.1:8000/api/turmas/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"nome":"7A","ano_letivo":2026,"disciplina":1,"unidade":1}'
```

Guarde o `id` retornado como `turma_id`.

#### 4) Criar aluno

```bash
curl -X POST http://127.0.0.1:8000/api/alunos/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Ana Souza","matricula":"2026-0001","email":"ana@example.com","turma":1,"ativo":true}'
```

Guarde o `id` retornado como `aluno_id`.

#### 5) Criar avaliação

```bash
curl -X POST http://127.0.0.1:8000/api/avaliacoes/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Prova 1","tipo":"mensal","turma":1,"peso":"2.00","data_aplicacao":"2026-03-10","prazo_entrega":"2026-03-12","penalidade_atraso":"0.50"}'
```

Guarde o `id` retornado como `avaliacao_id`.

#### 6) Lançar nota

```bash
curl -X POST http://127.0.0.1:8000/api/notas/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"aluno":1,"avaliacao":1,"valor":"8.75","entregue_em":"2026-03-11"}'
```

#### 7) Consultar dashboard da turma

```bash
curl http://127.0.0.1:8000/api/dashboard/turma/1/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Valide no retorno:
- `media_geral`
- `total_alunos`
- `total_avaliacoes`

### 6.5 Testar transferência de aluno entre turmas

1. Crie uma segunda turma (`id = 2`, por exemplo).
2. Execute a transferência:

```bash
curl -X POST http://127.0.0.1:8000/api/turmas/2/transferir_aluno/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"aluno_id":1}'
```

3. Consulte o aluno e confirme que `turma` mudou para `2`.

### 6.6 Teste via Django Admin (opcional)

1. Crie superusuário:

```bash
python manage.py createsuperuser
```

2. Acesse `http://127.0.0.1:8000/admin/`.
3. Valide CRUD de `Disciplina`, `Unidade`, `Turma`, `Aluno`, `Avaliacao` e `Nota`.

### 6.7 Checks técnicos rápidos

```bash
python manage.py check
python manage.py test
```

Observação: `test` ainda está com suíte mínima (sem cenários de negócio completos), mas já pode ser usado como baseline de evolução.

## 7) Troubleshooting rápido

### 7.1 Recebi `401 Unauthorized` em `/api/disciplinas/`

Isso é esperado sem token JWT. Faça login em `/api/users/token/`, pegue `access` e envie no header `Authorization: Bearer <token>`.

### 7.2 Recebi erro dizendo que `id` é obrigatório

No backend, os modelos usam `BigAutoField` (auto incremento). O `id` deve ser retornado na resposta, nunca exigido no request de criação.

Se sua ferramenta estiver pedindo `id` no POST:
- remova `id` do body manualmente;
- force atualização do schema da ferramenta;
- reinicie o servidor Django para recarregar alterações de serializers.
