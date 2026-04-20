# Guia para Agente Externo — Serviço dedicado de IA com URL pública (Netlify) + RAG

Data: 12/03/2026

## 1) Objetivo deste guia

Este documento orienta um agente externo a construir um **serviço dedicado de IA** (separado deste repositório), publicar em URL e manter compatibilidade com o backend atual.

Decisão de arquitetura deste projeto:

- este repositório continua responsável por **integração**;
- o outro agente entrega um serviço de IA autônomo, publicado e observável;
- comunicação via HTTP através de `LOCAL_LLM_BASE_URL`.

## 2) Modelo LLM gratuito escolhido

Modelo padrão obrigatório para a primeira versão:

- **Qwen/Qwen2.5-7B-Instruct**

Justificativa:

- boa qualidade em PT-BR para instrução/resumo;
- open-source e gratuito para uso local;
- possui suporte amplo em runtime open-source.

Observação importante sobre Netlify:

- Netlify **não é ambiente ideal para inferência pesada de LLM** (GPU).
- Em produção prática, usar:
  - Netlify para API pública/orquestração;
  - backend de inferência em serviço compatível (ex.: instância com Ollama/GPU).

Se houver limitação de infra, o agente pode começar com provider remoto gratuito para bootstrap, mantendo a mesma interface de API.

## 3) Contrato que o serviço precisa expor (compatibilidade obrigatória)

O backend atual espera endpoint no formato Ollama-like:

### 3.1 Healthcheck

- `GET /health`

Resposta esperada (200):

```json
{
  "status": "ok",
  "service": "ia-dedicada"
}
```

### 3.2 Geração

- `POST /api/generate`

Request mínimo esperado:

```json
{
  "model": "qwen2.5:7b-instruct",
  "prompt": "texto",
  "stream": false,
  "options": {
    "temperature": 0.2
  }
}
```

Response mínima esperada:

```json
{
  "response": "texto gerado"
}
```

Se houver erro, retornar HTTP 4xx/5xx com payload consistente.

## 4) Escopo técnico da entrega do agente externo

### Fase A — Serviço mínimo em produção (MVP)

1. Criar serviço dedicado de IA (repo separado).
2. Expor `GET /health` e `POST /api/generate`.
3. Publicar URL funcional (Netlify como camada pública).
4. Integrar modelo Qwen2.5-7B-Instruct no runtime escolhido.
5. Configurar timeout, limites de payload e logs básicos.

Critério de aceite:

- URL pública respondendo `health` e `generate`;
- backend deste projeto consegue chamar o endpoint via `LOCAL_LLM_BASE_URL`.

### Fase B — RAG semântico dedicado

1. Implementar ingestão de documentos/contexto (entrada textual estruturada).
2. Gerar embeddings e armazenar em vetor store.
3. Recuperar contexto por similaridade (`top_k`).
4. Montar prompt final com fontes recuperadas.
5. Retornar resposta + metadados de fontes.

Critério de aceite:

- melhora perceptível de relevância nas respostas;
- retorno rastreável com fontes.

### Fase C — Operação e confiabilidade

1. Logs estruturados (request_id, latência, status, modelo).
2. Métricas de sucesso/erro/latência.
3. Retry controlado e circuit breaker simples.
4. Limite de taxa por IP/token.

Critério de aceite:

- serviço monitorável e estável para uso contínuo.

## 5) Padrão de variáveis de ambiente do serviço externo

Obrigatórias:

- `LLM_MODEL=Qwen/Qwen2.5-7B-Instruct`
- `LLM_TEMPERATURE=0.2`
- `LLM_TIMEOUT_SECONDS=60`
- `RAG_TOP_K_DEFAULT=6`
- `RAG_MAX_TOP_K=20`
- `SERVICE_API_KEY=<segredo>`

Para integração com este backend:

- `LOCAL_LLM_ENABLED=True`
- `LOCAL_LLM_BASE_URL=<URL_PUBLICA_DO_SERVICO_IA>`
- `LOCAL_LLM_MODEL=qwen2.5:7b-instruct`

## 6) Segurança mínima obrigatória

1. Exigir chave de API no serviço externo (`Authorization: Bearer ...` ou `x-api-key`).
2. Não registrar prompt/resposta completos em logs de produção.
3. Sanitizar entrada para evitar abuso de payload.
4. Habilitar CORS apenas para origens permitidas.

## 7) Plano de validação

Checklist de testes do serviço externo:

1. `GET /health` retorna 200.
2. `POST /api/generate` com prompt simples retorna `response`.
3. timeout e erros de provider retornam status coerente.
4. carga básica (teste concorrente curto) sem falhas graves.

Checklist de integração com este backend:

1. configurar `LOCAL_LLM_BASE_URL` para a URL pública;
2. chamar endpoint de insights deste sistema;
3. validar resposta final e tratamento de erro em indisponibilidade.

## 8) Entregáveis esperados do agente externo

1. Repositório do serviço de IA.
2. URL pública funcional.
3. README com setup local e deploy.
4. Documento de operação (monitoramento e troubleshooting).
5. Evidências de teste (prints/logs/resumo).

## 9) Definição de pronto (DoD)

Só considerar concluído quando:

- serviço publicado e acessível por URL;
- contrato `/health` e `/api/generate` compatível;
- modelo Qwen2.5-7B-Instruct configurado;
- segurança mínima aplicada;
- integração com este backend validada ponta a ponta.

## 10) Limites desta iniciativa

- Não treinar LLM do zero nesta fase.
- Prioridade: entrega de serviço dedicado, estável e integrável.
- Evolução posterior: fine-tuning, cache semântico e otimização de custo/latência.

## 11) Retomada imediata (próximas ações do agente externo)

Executar nesta ordem, sem pular etapas:

1. Subir MVP compatível com `GET /health` e `POST /api/generate`.
2. Proteger o endpoint com chave (`Authorization: Bearer` ou `x-api-key`).
3. Publicar URL pública e validar healthcheck externo.
4. Rodar teste de geração com payload mínimo compatível.
5. Enviar para este projeto as variáveis finais de integração:
  - `LOCAL_LLM_ENABLED=True`
  - `LOCAL_LLM_BASE_URL=<URL_PUBLICA_DO_SERVICO_IA>`
  - `LOCAL_LLM_MODEL=qwen2.5:7b-instruct`
6. Executar validação ponta a ponta a partir do backend deste repositório.

Evidências obrigatórias da retomada:

- URL pública respondendo 200 em `/health`.
- Exemplo real de request/response em `/api/generate`.
- Confirmação de timeout e tratamento de erro.
