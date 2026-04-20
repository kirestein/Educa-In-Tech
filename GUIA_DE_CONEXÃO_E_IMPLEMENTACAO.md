# Guia de Conexão e Implantação para Desenvolvedores

Este documento descreve como configurar a aplicação para se conectar ao banco de dados Neon e ao armazenamento Cloudflare R2, além de sugerir opções de hospedagem para a API. Os exemplos usam variáveis de ambiente para evitar expor segredos.

1. Configurando o banco de dados (Neon)
   1.1 String de conexão

O Neon fornece um banco de dados PostgreSQL serverless. A aplicação deve usar a connection string fornecida pelo projeto. Armazene esse valor numa variável de ambiente, por exemplo DATABASE_URL:

## Arquivo .env

DATABASE_URL="postgresql://<USUARIO>:<SENHA>@ep-<hash>.c-2.us-east-1.aws.neon.tech/<NOME_DO_BANCO>?sslmode=require&channel_binding=require"

Substitua <USUARIO>, <SENHA> e <NOME_DO_BANCO> pelos valores da sua string. No caso da string enviada pelo cliente, ela já contém todos os parâmetros; basta copiá-la integralmente para DATABASE_URL.

1.2 Uso em frameworks (Django/Python)

Em aplicações Django, utilize a biblioteca dj-database-url para ler a DATABASE_URL e configurar o banco:

## settings.py

import dj_database_url
import os

DATABASES = {
'default': dj_database_url.parse(
os.environ.get('DATABASE_URL'),
conn_max_age=600, # persiste conexões para reduzir latência
)
}

O parâmetro sslmode=require garante a conexão segura via TLS. A opção channel_binding=require habilita a validação de canal (necessária para alguns drivers). Para Node.js, use o pacote pg ou @neondatabase/serverless com a mesma DATABASE_URL.

1.3 Considerações sobre Neon

Neon oferece apenas o serviço de banco de dados; não hospeda a API. Em um relato de uso do Neon para um curso on‑line, o autor hospedou o application server no Fly.io enquanto o banco de dados permaneceu no Neon; ambos estavam na mesma região para minimizar latência. Portanto, para expor sua API você precisará de um provedor de compute separado (ver seção de hospedagem).

2. Configurando o armazenamento de objetos (Cloudflare R2)

O R2 é um serviço de armazenamento S3‑compatível. Para acessá‑lo através de bibliotecas S3 (AWS SDK, boto3, rclone), você precisará de um Access Key ID e um Secret Access Key. Esses valores são derivados de um token de API da conta.

2.1 Criando um token de API

No painel da Cloudflare, ative o R2 e navegue até R2 Object Storage.

Clique em Manage API tokens e escolha Create API token.

Selecione Account API token ou User API token, conforme sua necessidade. Tokens de conta podem ser usados por qualquer serviço autorizado e permanecem válidos até revogação.

Nas permissões, escolha Workers R2 Storage Write ou Object Read & Write, permitindo criar buckets e enviar/baixar objetos. Opcionalmente, limite o token a buckets específicos.

Após confirmar, a interface exibirá o Access Key ID (ID do token) e o Secret Access Key (hash SHA‑256 do token). O segredo só é mostrado uma vez, então copie e armazene em local seguro.

O account_id que aparece no painel é usado apenas na URL do endpoint (https://<ACCOUNT_ID>.r2.cloudflarestorage.com) — ele não substitui o Access Key ID.

Se você já tem um token existente, verifique-o via API:

curl "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/tokens/verify" \
 -H "Authorization: Bearer <CLOUDFLARE_API_TOKEN>"

A resposta deve conter "success": true se o token estiver válido.

2.2 Derivando as credenciais S3

O Access Key ID e o Secret Access Key são derivados do token. O primeiro corresponde ao ID do token; o segundo é o hash SHA‑256 do valor do token. No Linux/macOS você pode gerar o segredo assim:

## Gere o segredo a partir do valor do token

printf '%s' "$CLOUDFLARE_API_TOKEN" | sha256sum | awk '{print $1}'

Configure as seguintes variáveis de ambiente no back‑end:

AWS_ACCESS_KEY_ID=<ACCESS_KEY_ID> # ID do token gerado
AWS_SECRET_ACCESS_KEY=<SECRET_ACCESS_KEY> # Hash SHA-256 do token
R2_ENDPOINT="https://<ACCOUNT_ID>.r2.cloudflarestorage.com" # Endpoint S3
R2_REGION="auto" # Região 'auto' para R2 (ou 'us-east-1' conforme o SDK)
BUCKET_NAME=<NOME_DO_BUCKET>
2.3 Integração com Django (django‑storages)

Para enviar e servir arquivos pelo R2 em um projeto Django, utilize django-storages com a backend S3:

Instale as dependências: pip install boto3 django-storages.

Adicione 'storages' ao INSTALLED_APPS.

Configure as variáveis no settings.py:

## settings.py (exemplo)

AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('R2_REGION', 'auto')
AWS_S3_ADDRESSING_STYLE = 'virtual' # requerido para Cloudflare

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

Esse backend fará upload/download de arquivos (provas digitalizadas, relatórios, etc.) diretamente no R2.

3. Modelo de variáveis de ambiente

Crie um arquivo .env (ou configure variáveis no serviço de hospedagem) com os valores abaixo:

## Banco de dados Neon

DATABASE_URL=postgresql://<USUARIO>:<SENHA>@ep-<hash>.c-2.us-east-1.aws.neon.tech/<NOME_DO_BANCO>?sslmode=require&channel_binding=require

## Cloudflare R2

ACCOUNT_ID=<ACCOUNT_ID>
CLOUDFLARE_API_TOKEN=<TOKEN_DO_R2>
AWS_ACCESS_KEY_ID=<ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<SECRET_ACCESS_KEY>
R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_REGION=auto
BUCKET_NAME=<NOME_DO_BUCKET>

## Outras configurações (ex.: Django)

SECRET_KEY=<CHAVE_SECRETA_DJANGO>
DEBUG=False # desative em produção
ALLOWED_HOSTS=localhost, 127.0.0.1

Lembre-se de nunca versionar este arquivo; use um gerenciador de segredos na plataforma de hospedagem.

Importante: se alguma credencial já foi exposta em commit, considere-a comprometida e faça rotação imediata (senha do banco, token e chaves derivadas).

4. Opções de hospedagem para a API

Neon fornece apenas o banco de dados, portanto você deve implantar a API (Python/Node.js) em outra plataforma. A seguir, algumas opções de baixo custo e suas características:

4.1 Render

O Render é um PaaS moderno que abstrai a infraestrutura e oferece deploy contínuo via Git, gerenciamento automático de certificados SSL e proteção DDoS. A plataforma possui integração nativa com PostgreSQL e Redis; dorme serviços inativos em ambientes de desenvolvimento e os acorda sob demanda, otimizando custos. Há um plano gratuito para web services básicos; o plano pago começa em US$ 19/mês.

4.2 Fly.io

O Fly.io distribui aplicações por regiões globais para reduzir latência e oferece WebSocket support e bancos PostgreSQL integrados. Seu modelo é pay‑as‑you‑go; uma aplicação simples custa cerca de US$ 15/mês. O relato sobre Neon citado acima hospedou o servidor da aplicação no Fly.io, mantendo o banco em Neon.

4.3 Cloudflare Pages + Workers

Para um modelo totalmente serverless, Cloudflare combina Pages (static hosting) com Workers (funções edge). A cota gratuita inclui sites ilimitados, requisições ilimitadas e até 100.000 invocações de Workers por dia. A plataforma integra-se diretamente a serviços da própria Cloudflare, como R2, KV e D1, e oferece CDN global com zero cold starts. Essa opção é indicada para aplicações JAMstack ou APIs pequenas.

4.4 Railway

Railway oferece implantação fácil a partir de repositórios Git e suporte a bancos integrados. A plataforma fornece ambientes de pré-visualização automáticos para cada pull request e escalonamento horizontal com até 50 réplicas. A camada gratuita inclui US$ 5 de crédito/mês, 512 MB de RAM e 1 GB de disco, sendo adequada para MVPs. Planos pagos começam em US$ 5/mês.

4.5 Outras opções

Cloudflare Workers Unbound: ideal para funções rápidas sem servidor; cota gratuita de 100k invocações/dia.

Heroku: a plataforma clássica PaaS; não possui mais plano gratuito para apps, com preços a partir de US$ 5/mês, mas oferece add-ons e pipelines maduros.

5. Recomendações finais

Segurança de credenciais – Nunca exponha tokens ou senhas em repositórios. Use variáveis de ambiente e gerenciadores de segredos da plataforma de hospedagem.

Manter as regiões próximas – Coloque a API na mesma região da instância Neon (por exemplo, us‑east‑1) para reduzir latência.

Monitoramento de custos – O Neon possui 100 horas de computação na camada gratuita; use-a para desenvolvimento e desligue serviços em período de baixa. Avalie se um VPS fixo (~US$ 5/mês) não compensa para uso contínuo.

Escalabilidade futura – Caso o tráfego aumente, considere migrar para planos pagos ou serviços que suportem auto‑scaling mais agressivo, como Cloudflare Workers ou Railway.

6. Passo a passo rápido no projeto atual (Educa in Tech)

Use este roteiro para aplicar a configuração no backend Django existente:

1. Crie o arquivo app/.env com as variáveis necessárias (DATABASE_URL e, se usar storage, variáveis do R2).
2. Ative o ambiente virtual do projeto e instale dependências:
   - pip install -r app/requirements.txt
3. A partir de app/backend, execute:
   - python manage.py check
   - python manage.py migrate
4. Inicie a API:
   - python manage.py runserver
5. Valide healthcheck:
   - GET http://127.0.0.1:8000/api/health/
6. Se quiser usar o serviço externo de IA, adicione no mesmo .env:
   - LOCAL_LLM_ENABLED=True
   - LOCAL_LLM_BASE_URL=<URL_PUBLICA_DO_SERVICO_IA>
   - LOCAL_LLM_MODEL=qwen2.5:7b-instruct
   - LOCAL_LLM_TIMEOUT_SECONDS=60
   - LOCAL_LLM_TEMPERATURE=0.2

Compatibilidade de variáveis:

- `OLLAMA_BASE_URL` também é aceito como alias de `LOCAL_LLM_BASE_URL`.
- `SERVICE_API_KEY` também é aceito como alias de `LOCAL_LLM_API_KEY`.

Segurança opcional para provider externo:

- `LOCAL_LLM_API_KEY=<token>`
- `LOCAL_LLM_AUTH_HEADER=Authorization` (ou `x-api-key`)
- `LOCAL_LLM_USE_BEARER=True` (quando header for Authorization)

Esse mapeamento é compatível com as configurações já lidas no backend (DATABASE*URL e variáveis LOCAL_LLM*\*).

7. Plano de migração local -> banco online (sem perder conhecimento)

Sim, é possível começar local e migrar depois sem perder o que o sistema aprendeu via RAG.
Para isso, trate conhecimento como dado persistido: documentos, chunks, embeddings e metadados versionados.

7.1 Princípio de segurança

- Não depender de memória da sessão do LLM.
- Persistir tudo em banco + storage de arquivos.
- Fazer backup antes de qualquer corte.
- Validar contagens e consultas de busca após restore.

  7.2 O que precisa ser migrado

1. Dados transacionais da aplicação (tabelas Django).
2. Dados de conhecimento/RAG (documents, chunks, embeddings, metadados).
3. Arquivos-fonte (PDF, planilhas, anexos) no bucket/pasta de storage.
4. Configurações de ambiente (DATABASE_URL, endpoint LLM, chaves e parâmetros).

7.3 Estratégia recomendada para este projeto

- Fase inicial local: PostgreSQL local (de preferência já com pgvector) ou SQLite para MVP curto.
- Fase online: Neon PostgreSQL.
- Storage: Cloudflare R2 (evita mover arquivos no momento da troca do banco).

  7.4 Pré-checklist da migração

1. Congelar escrita na aplicação (janela de manutenção curta).
2. Confirmar versão do Django e migrations aplicadas.
3. Garantir que o banco destino está acessível via DATABASE_URL.
4. Gerar backup de banco e inventário de arquivos.
5. Registrar hash/checksum do backup para auditoria.

7.5 Caminho A (recomendado): PostgreSQL local -> Neon PostgreSQL

Backup local:

```bash
pg_dump "$LOCAL_DATABASE_URL" -Fc -f backup_local.dump
```

Restore no Neon:

```bash
pg_restore --no-owner --no-privileges --clean --if-exists \
   -d "$DATABASE_URL_NEON" backup_local.dump
```

Aplicar migrations pendentes (se necessário):

```bash
cd app/backend
python manage.py migrate
```

7.6 Caminho B: SQLite local -> Neon PostgreSQL

Exportar dados do SQLite:

```bash
cd app/backend
python manage.py dumpdata \
   --natural-foreign --natural-primary \
   -e contenttypes -e auth.permission \
   > backup_sqlite.json
```

Apontar DATABASE_URL para Neon, criar estrutura e importar:

```bash
cd app/backend
python manage.py migrate
python manage.py loaddata backup_sqlite.json
```

Observação: para bases grandes, prefira PostgreSQL local desde cedo e use o Caminho A.

7.7 Validação pós-migração (obrigatória)

1. `python manage.py check`
2. Validar login JWT e endpoints críticos.
3. Comparar contagens principais antes/depois (ex.: alunos, turmas, avaliações, notas).
4. Executar 3 consultas RAG conhecidas e comparar relevância.
5. Verificar latência e erros em logs.

7.8 Plano de rollback

Se a validação falhar:

1. Reapontar `DATABASE_URL` para o banco anterior.
2. Restaurar backup do estado pré-corte.
3. Reabrir escrita apenas após nova validação.

7.9 Boas práticas para não perder conhecimento no futuro

- Versionar documentos e chunks por `source_id` e `version`.
- Registrar `embedding_model`, `embedding_dim` e data de indexação.
- Se trocar modelo de embedding, executar reindexação completa.
- Manter backups automáticos e teste periódico de restore.

8. Automação local pronta no repositório

Foram adicionados scripts para operação local em:

- `app/backend/scripts/init_local_env.sh`
- `app/backend/scripts/backup_local.sh`
- `app/backend/scripts/restore_local.sh`

Checklist semanal operacional:

- `CHECKLIST_OPERACAO_LOCAL_SEMANAL.md`

  8.1 Backup local

```bash
cd app/backend
./scripts/backup_local.sh
```

Comportamento:

- Se `DATABASE_URL` for PostgreSQL, gera dump `.dump` via `pg_dump`.
- Caso contrário, faz cópia do SQLite (`db.sqlite3`).
- Gera hash `.sha256` quando utilitário de hash estiver disponível.

  8.2 Restore local

```bash
cd app/backend
./scripts/restore_local.sh <arquivo_backup>
```

Opções:

- `--force`: não pede confirmação interativa.
- `--skip-migrate`: pula `python manage.py migrate` após restore.

Exemplo (não interativo):

```bash
cd app/backend
./scripts/restore_local.sh backups/sqlite_YYYYMMDD_HHMMSS.sqlite3 --force
```

8.3 Smoke test do endpoint LLM-RAG

Script disponível em:

- `app/backend/scripts/smoke_test_llm.sh`

Uso padrão:

```bash
cd app/backend
./scripts/smoke_test_llm.sh
```

8.4 Start + teste em um comando

Script disponível em:

- `app/backend/scripts/start_local_and_test_llm.sh`

Esse script executa: `check` -> `migrate` -> `runserver` -> espera `health` -> smoke test LLM.

Se `app/.env` não existir, ele inicializa automaticamente um `.env` local padrão.

Se a porta `8000` estiver ocupada, ele escolhe automaticamente a próxima porta livre.

Por padrão, ele também garante usuários demo para autenticação no smoke test.

Credenciais padrão usadas:

- `professor_demo` / `Professor@12345`
- `coordenador_demo` / `Coordenador@12345`
- `admin` / `Admin@12345`

Uso padrão:

```bash
cd app/backend
./scripts/start_local_and_test_llm.sh
```

Variáveis úteis:

- `START_SERVER=false`: usa servidor já rodando.
- `RUN_MIGRATIONS=false`: pula migrations.
- `SEED_DEMO_USERS=false`: não cria/atualiza usuários demo.
- `AUTO_INIT_ENV=false`: não cria `.env` automaticamente.
- `WAIT_SECONDS=60`: aumenta tempo de espera do health.
- `HOST` e `PORT`: muda bind do `runserver`.

Exemplo com servidor já iniciado:

```bash
cd app/backend
START_SERVER=false BASE_URL=http://127.0.0.1:8000 ./scripts/start_local_and_test_llm.sh
```

9. Persistência dedicada de conhecimento RAG (implementada)

Foi adicionada persistência versionada de conhecimento no backend:

- `KnowledgeDocument`: documento lógico da base de conhecimento.
- `KnowledgeChunk`: fragmentos do documento usados no contexto RAG.

Comportamento atual no endpoint de insights:

1. A cada geração de insights por turma, o backend salva (ou reaproveita) um snapshot versionado dos chunks de contexto.
2. Se o conteúdo não mudou (checksum igual), a versão anterior é reutilizada.
3. Se mudou, é criada nova versão e a anterior fica inativa.

Endpoints disponíveis:

- `GET /api/knowledge/documents/`
- `GET /api/knowledge/chunks/`
- `GET /api/knowledge/chunks/?document_id=<id>`
- `POST /api/knowledge/documents/ingest-text/`

Filtros úteis:

- `GET /api/knowledge/documents/?source_id=<source_id>&source_type=<tipo>&turma_id=<id>&is_active=true`
- `GET /api/knowledge/chunks/?source_id=<source_id>&source_type=<tipo>`

Permissões:

- leitura: usuário autenticado;
- escrita: coordenador/admin.

Rastreabilidade no retorno de insights:

- `knowledge_document_id`
- `knowledge_document_version`

  9.1 Ingestão manual de conhecimento por texto

Payload mínimo:

```json
{
  "source_id": "manual:politica-avaliacao:2026-03",
  "source_type": "manual",
  "title": "Política de avaliação",
  "text": "Texto completo do conhecimento..."
}
```

Campos opcionais:

- `turma_id`
- `chunk_size` (200-4000, default 800)

  9.2 Export/import de conhecimento para migração local -> online

Scripts:

- `app/backend/scripts/export_knowledge.sh`
- `app/backend/scripts/import_knowledge.sh`

Exportar:

```bash
cd app/backend
./scripts/export_knowledge.sh
```

Importar:

```bash
cd app/backend
./scripts/import_knowledge.sh backups/knowledge_export_YYYYMMDD_HHMMSS.json
```

Importar substituindo conhecimento existente no destino:

```bash
cd app/backend
./scripts/import_knowledge.sh backups/knowledge_export_YYYYMMDD_HHMMSS.json --replace
```

10. Sistema pronto para rodar local (um comando)

Script principal:

- `app/backend/scripts/run_local_ready_demo.sh`

O que ele faz automaticamente:

1. check + migrate;
2. seed de usuários demo;
3. seed de dados acadêmicos mínimos;
4. sobe API local;
5. autentica com admin;
6. ingere conhecimento manual de exemplo;
7. executa busca no acervo e imprime resultado.

Executar:

```bash
cd app/backend
./scripts/run_local_ready_demo.sh
```

Opcional (tentar insights LLM também):

```bash
cd app/backend
RUN_LLM_INSIGHTS=true ./scripts/run_local_ready_demo.sh
```

Observação para máquinas com pouca RAM:

- O modo local usa por padrão um modelo leve (`qwen2.5:0.5b`) para garantir que os insights rodem sem erro de memória.
- Se quiser testar outro modelo, passe `LOCAL_LLM_MODEL=<modelo>` na execução.

Variáveis opcionais para personalizar o teste:

- `BASE_URL` (default: `http://127.0.0.1:8000`)
- `AUTH_USERNAME` (default: `professor_demo`)
- `AUTH_PASSWORD` (default: `Professor@12345`)
- `TURMA_ID` (default: `1`)
- `PERGUNTA` (prompt de teste)

Exemplo:

```bash
cd app/backend
BASE_URL=http://127.0.0.1:8000 \
AUTH_USERNAME=professor_demo \
AUTH_PASSWORD=Professor@12345 \
TURMA_ID=1 \
PERGUNTA='Quais ações priorizar na próxima semana?' \
./scripts/smoke_test_llm.sh
```

Referências: Este guia baseia‑se na documentação do Cloudflare R2 para criação de tokens, no relato de uso do Neon demonstrando que a aplicação foi hospedada no Fly.io, e na análise de plataformas de hospedagem feita pela RunCloud, que descreve características e limites de Render, Fly.io, Cloudflare Pages/Workers e Railway.
