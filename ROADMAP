# ROADMAP — Educa in Tech

Data de referência: 12 de março de 2026

## 1. Visão geral

Este documento consolida:

- tudo o que já foi entregue no projeto até agora;
- o que está validado tecnicamente;
- o que ainda precisa ser feito;
- a ordem sugerida das próximas entregas.

---

## 2. Entregas concluídas

### 2.1 Estrutura inicial do backend

- Backend Django criado em `app/backend`.
- Configuração principal do projeto em `config`.
- Banco local com SQLite configurado para desenvolvimento.
- Suporte preparado para PostgreSQL via variáveis de ambiente.

### 2.2 Modelagem do domínio acadêmico

Implementado em `app/backend/core/models.py`:

- `Disciplina`
- `Unidade`
- `Turma`
- `Aluno`
- `Avaliacao`
- `Nota`

Regras já entregues:

- relacionamentos entre entidades do domínio;
- constraints de unicidade para evitar duplicidade;
- chaves primárias automáticas com `BigAutoField`;
- regras básicas de integridade para notas, turmas e vínculos acadêmicos.

### 2.3 API REST do domínio

Implementado em `app/backend/core`:

- serializers para todas as entidades;
- viewsets com CRUD para os recursos principais;
- rotas REST com router DRF;
- endpoint de healthcheck;
- endpoint de dashboard por turma;
- endpoint para transferência de aluno entre turmas.

### 2.4 Autenticação e módulo de usuários

Implementado em `app/backend/users`:

- autenticação JWT com access e refresh token;
- endpoint `/api/users/token/`;
- endpoint `/api/users/token/refresh/`;
- endpoint `/api/users/me/`;
- endpoint `/api/users/roles/assign/`;
- healthcheck do módulo `users`.

### 2.5 Permissões e RBAC refinado

Implementado e validado:

- leitura autenticada (`list`/`retrieve`) nos viewsets principais do `core`;
- escrita restrita por papel (`admin`/`coordenador` e `professor` conforme endpoint);
- permissões customizadas no app `core` aplicadas por ação (`get_permissions`);
- proteção administrativa para atribuição de roles em `users`;
- cenários positivos e negativos de autorização cobertos com testes.

### 2.6 Admin Django

Implementado em `app/backend/core/admin.py`:

- registro dos modelos do domínio;
- filtros, listagens e campos de busca para operação administrativa.

### 2.7 Migrações

- Migração inicial criada para o domínio acadêmico.
- Estrutura validada com `manage.py migrate` e `manage.py check`.

### 2.8 Testes automatizados

Testes gerados com sucesso em:

- `app/backend/core/tests.py`
- `app/backend/users/tests.py`

Cobertura atual inclui:

- testes de modelo;
- testes de autenticação JWT;
- testes de endpoints protegidos;
- testes de CRUD;
- testes de transferência de aluno;
- testes do dashboard;
- testes de atribuição de roles.

Status validado:

- **50 testes passando**.

### 2.9 Pipeline CI/CD

Implementado:

- workflow do GitHub Actions para validação do backend;
- instalação de dependências;
- `manage.py check`;
- validação de migrações;
- execução dos testes;
- verificação informativa de estilo.

Correções já aplicadas no CI:

- ajuste da matrix Python para versões compatíveis com Django 6.x;
- definição de `STATIC_ROOT` para permitir `collectstatic` no pipeline.

### 2.10 Git e organização do repositório

Concluído:

- branch `main` criada e definida como branch padrão do repositório;
- branch de trabalho `feat/backend-bootstrap-academic-api` em uso;
- branch de refinamento `feat/rbac-refinamento` criada e publicada no remoto;
- convenção de commits aplicada;
- pushes e correções do pipeline enviados ao remoto.

### 2.11 Documentação de acesso por papel (RBAC)

Concluído:

- matriz de acesso por endpoint/método documentada em `RBAC_ACCESS_MATRIX.md`;
- papéis `autenticado`, `professor`, `coordenador` e `admin` formalizados;
- regras de leitura/escrita e ações customizadas registradas como referência de produto e backend.

### 2.12 Dashboards analíticos (primeira evolução)

Concluído:

- dashboard de turma expandido com distribuição de notas por faixa;
- inclusão de cobertura de lançamento de notas (total e percentual);
- inclusão de média por tipo de avaliação no endpoint de dashboard;
- testes do dashboard ampliados para cenários com e sem notas.

### 2.13 Padronização de erros e contrato de API

Concluído:

- contrato de erro padronizado com envelope único para autenticação, permissão, validação e not found;
- handler global de exceções DRF configurado para respostas consistentes;
- endpoints customizados de `core` e `users` ajustados para o mesmo formato de erro;
- testes ampliados para validar o payload padronizado dos principais cenários de falha.

### 2.14 Documentação OpenAPI / Swagger

Concluído:

- integração de `drf-spectacular` ao backend Django/DRF;
- endpoint de schema publicado em `/api/schema/`;
- Swagger UI publicado em `/api/docs/`;
- configuração base de metadados OpenAPI adicionada ao projeto;
- testes de disponibilidade do schema e da interface Swagger adicionados.

---

## 3. O que está validado neste momento

Validado localmente:

- `manage.py check`;
- `manage.py collectstatic --noinput --dry-run`;
- suíte de testes com 50/50 passando.

Validado estruturalmente:

- autenticação JWT operacional;
- warning de chave JWT curta resolvido com `SIMPLE_JWT['SIGNING_KEY']` e chave mínima adequada;
- endpoints principais publicados;
- regras de permissão por papel refinadas e testadas;
- CI ajustado para compatibilidade com o stack atual.

---

## 4. Tarefas em andamento ou atenção imediata

### 4.1 Confirmar PR totalmente verde

Com as mudanças de RBAC e JWT já publicadas na branch de refinamento, é importante confirmar no GitHub que:

- todos os checks ficaram verdes;
- o PR está apto para merge;
- não há novo erro de ambiente ou configuração.

---

## 5. Próximas tarefas recomendadas

### Prioridade 1 — Dashboards mais avançados (fase 2)

Próximas evoluções sugeridas:

- recortes por período;
- tendências/séries históricas;
- indicadores comparativos entre turmas.

### Prioridade 2 — Integrações externas

Backlog planejado:

- integração com Google Sheets;
- integração com microserviço de IA;
- sincronizações futuras com serviços externos.

### Prioridade 3 — Endurecimento para produção

Evoluções recomendadas:

- segurança adicional e gestão de segredos;
- observabilidade e logs estruturados;
- ajustes de deploy e configuração por ambiente.

---

## 6. Backlog estratégico

Itens ainda não iniciados ou não concluídos:

- dashboards analíticos avançados (fase 2);
- integração com Google Sheets;
- integração backend ↔ microserviço de IA;
- endurecimento para produção (segurança, observabilidade e configurações de deploy).

---

## 7. Respostas objetivas

### Os testes foram gerados?

Sim.

Arquivos:

- `app/backend/core/tests.py`
- `app/backend/users/tests.py`

Status validado:

- **50 testes passando**.

### O próximo passo é evoluir dashboards da turma (fase 2)?

Sim.

Com RBAC, contrato de erros e OpenAPI já entregues, a próxima frente de maior valor é aprofundar a camada analítica com recortes temporais e indicadores comparativos.

---

## 8. Resumo executivo

Projeto já entregue até aqui:

- backend funcional;
- autenticação JWT;
- API REST principal;
- permissões por papel refinadas (RBAC);
- testes automatizados;
- CI/CD ativo;
- branch principal organizada.

Próximo foco recomendado:

- **evoluir dashboards analíticos na fase 2 e preparar integrações externas**.
