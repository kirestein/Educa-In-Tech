# Checklist Semanal de Operacao Local

Objetivo: manter ambiente local confiavel e pronto para migracao sem perda de dados/conhecimento.

## 1) Backup e restauracao

1. Rodar backup local:
   - cd app/backend
   - ./scripts/backup_local.sh
2. Verificar se arquivo foi criado em app/backend/backups.
3. Verificar se hash .sha256 foi gerado.
4. Executar teste de restore em ambiente de homologacao local (nao no ambiente em uso do time).

## 2) Integridade de dados

1. Comparar contagens basicas apos restore de teste:
   - turmas
   - alunos
   - avaliacoes
   - notas
2. Validar 3 consultas RAG conhecidas e comparar resultado esperado.
3. Verificar se nao houve mudanca de embedding_model sem reindexacao.

## 3) Saude da aplicacao

1. Rodar:
   - cd app/backend
   - python manage.py check
   - python manage.py migrate
2. Testar endpoints:
   - /api/health/
   - /api/users/health/
   - /api/integrations/llm-rag/dashboard/turma/<id>/insights/
3. Confirmar que erros 5xx estao zerados no periodo.

## 4) Disciplina operacional

1. Garantir que app/.env nao foi versionado.
2. Rotacionar credenciais em caso de exposicao.
3. Registrar no changelog interno:
   - data do backup
   - nome do arquivo
   - status do teste de restore
   - pendencias encontradas

## 5) Critério para subir ambiente online

Subir apenas quando todos os itens abaixo estiverem verdadeiros:

1. Backups diarios estaveis por 7 dias.
2. Pelo menos 1 restore de teste validado por semana.
3. Endpoints criticos sem falha bloqueante.
4. Plano de rollback revisado e testado.
