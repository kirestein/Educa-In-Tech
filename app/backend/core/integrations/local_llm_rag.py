from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
import time
from typing import Any

import requests
from django.conf import settings
from django.db.models import Avg
from django.db import transaction

from core.models import Aluno, Avaliacao, KnowledgeChunk, KnowledgeDocument, Nota, Turma
from core.serializers import TurmaDashboardSerializer


logger = logging.getLogger(__name__)
_CIRCUIT_OPEN_UNTIL = 0.0
_CIRCUIT_FAILURES = 0


class LocalLLMConfigError(Exception):
    """Raised when local LLM integration is not configured."""


class LocalLLMExecutionError(Exception):
    """Raised when local LLM request fails."""


@dataclass
class RagChunk:
    title: str
    content: str


def _decimal_text(value: Any) -> str:
    if value is None:
        return '0.00'
    return f'{value}'


def _build_rag_chunks(*, turma: Turma, dias: int | None, top_k: int) -> list[RagChunk]:
    dashboard = TurmaDashboardSerializer.build(turma, dias=dias)

    chunks: list[RagChunk] = [
        RagChunk(
            title='Resumo da turma',
            content=(
                f"Turma: {turma.nome} ({turma.ano_letivo}) | Disciplina: {turma.disciplina.nome} | "
                f"Unidade: {turma.unidade.nome}. "
                f"Média geral: {dashboard['media_geral']}. "
                f"Total de alunos: {dashboard['total_alunos']}. "
                f"Total de avaliações: {dashboard['total_avaliacoes']}. "
                f"Cobertura de notas: {dashboard['percentual_notas_lancadas']}%."
            ),
        )
    ]

    for tipo_item in dashboard.get('media_por_tipo_avaliacao', []):
        chunks.append(
            RagChunk(
                title=f"Média por tipo ({tipo_item['tipo']})",
                content=f"Tipo {tipo_item['tipo']} com média {tipo_item['media']}.",
            )
        )

    for item in dashboard.get('serie_avaliacoes', [])[:top_k]:
        chunks.append(
            RagChunk(
                title=f"Avaliação recente: {item['titulo']}",
                content=(
                    f"Avaliação {item['titulo']} ({item['tipo']}) em {item['data_aplicacao']} "
                    f"com média {item['media']}."
                ),
            )
        )

    alunos_avg = (
        Aluno.objects.filter(turma=turma)
        .annotate(media_aluno=Avg('notas__valor'))
        .order_by('-media_aluno', 'nome')
    )
    melhores = [a for a in alunos_avg if a.media_aluno is not None][:top_k]
    piores = [a for a in alunos_avg.order_by('media_aluno', 'nome') if a.media_aluno is not None][:top_k]

    if melhores:
        chunks.append(
            RagChunk(
                title='Alunos com melhor média',
                content='; '.join(f"{a.nome}: {_decimal_text(a.media_aluno)}" for a in melhores),
            )
        )

    if piores:
        chunks.append(
            RagChunk(
                title='Alunos com menor média',
                content='; '.join(f"{a.nome}: {_decimal_text(a.media_aluno)}" for a in piores),
            )
        )

    pendentes = (
        Nota.objects.filter(avaliacao__turma=turma)
        .values('avaliacao__titulo')
        .annotate(total_lancadas=Avg('valor'))
    )
    if pendentes:
        chunks.append(
            RagChunk(
                title='Notas registradas',
                content=f"Foram encontradas {len(pendentes)} avaliações com notas registradas.",
            )
        )

    avaliacao_count = Avaliacao.objects.filter(turma=turma).count()
    chunks.append(
        RagChunk(
            title='Volume de avaliações',
            content=f"Quantidade total de avaliações cadastradas na turma: {avaliacao_count}.",
        )
    )

    return chunks[: max(1, min(top_k, settings.LOCAL_LLM_MAX_CONTEXT_DOCS))]


def _build_prompt(*, question: str, chunks: list[RagChunk]) -> str:
    rag_context = '\n\n'.join(f"[{i+1}] {chunk.title}\n{chunk.content}" for i, chunk in enumerate(chunks))
    return (
        'Você é um assistente acadêmico. Use somente os dados de contexto para responder. '\
        'Se faltar dado, diga explicitamente que não há dados suficientes. '\
        'Responda em português brasileiro, de forma objetiva e acionável.\n\n'
        f'Pergunta:\n{question}\n\n'
        f'Contexto RAG:\n{rag_context}\n\n'
        'Entregue:\n'
        '1) Diagnóstico curto\n'
        '2) 3 recomendações práticas\n'
        '3) 2 riscos de acompanhamento\n'
    )


def _build_chunks_checksum(*, source_id: str, chunks: list[RagChunk]) -> str:
    payload = '\n'.join(f"{c.title}\n{c.content}" for c in chunks)
    return hashlib.sha256(f'{source_id}\n{payload}'.encode('utf-8')).hexdigest()


@transaction.atomic
def persist_knowledge_chunks(
    *,
    source_id: str,
    source_type: str,
    title: str,
    chunks: list[RagChunk],
    turma: Turma | None = None,
    metadata: dict[str, Any] | None = None,
) -> KnowledgeDocument:
    checksum = _build_chunks_checksum(source_id=source_id, chunks=chunks)

    current = (
        KnowledgeDocument.objects.filter(source_id=source_id)
        .order_by('-version', '-id')
        .first()
    )
    if current and current.checksum == checksum:
        if not current.is_active:
            current.is_active = True
            current.save(update_fields=['is_active', 'updated_at'])
        return current

    next_version = (current.version + 1) if current else 1
    KnowledgeDocument.objects.filter(source_id=source_id, is_active=True).update(is_active=False)

    document = KnowledgeDocument.objects.create(
        source_id=source_id,
        source_type=source_type,
        title=title,
        version=next_version,
        checksum=checksum,
        turma=turma,
        metadata=metadata or {'chunk_count': len(chunks)},
        is_active=True,
    )

    KnowledgeChunk.objects.bulk_create(
        [
            KnowledgeChunk(
                document=document,
                position=index,
                title=chunk.title,
                content=chunk.content,
                token_count=len(chunk.content.split()),
                embedding_model='',
                embedding_dim=None,
                embedding_vector=[],
                metadata={'source': 'dashboard'},
            )
            for index, chunk in enumerate(chunks, start=1)
        ]
    )

    return document


def _build_llm_headers(*, request_id: str | None) -> dict[str, str]:
    headers = {'Content-Type': 'application/json'}
    api_key = (settings.LOCAL_LLM_API_KEY or '').strip()
    if api_key:
        header_name = settings.LOCAL_LLM_AUTH_HEADER or 'Authorization'
        if settings.LOCAL_LLM_USE_BEARER and header_name.lower() == 'authorization':
            headers[header_name] = f'Bearer {api_key}'
        else:
            headers[header_name] = api_key

    if request_id:
        headers['X-Request-Id'] = request_id
    return headers


def _candidate_models() -> list[str]:
    models = [settings.LOCAL_LLM_MODEL]
    fallback = (settings.LOCAL_LLM_FALLBACK_MODEL or '').strip()
    if fallback and fallback not in models:
        models.append(fallback)
    return models


def _ollama_generate(*, prompt: str, request_id: str | None = None) -> tuple[str, str]:
    global _CIRCUIT_FAILURES, _CIRCUIT_OPEN_UNTIL

    now = time.time()
    if _CIRCUIT_OPEN_UNTIL > now:
        remaining = int(_CIRCUIT_OPEN_UNTIL - now)
        raise LocalLLMExecutionError(
            f'Circuit breaker aberto para o provedor LLM local por mais {remaining}s.'
        )

    base_url = settings.LOCAL_LLM_BASE_URL.rstrip('/')
    url = f'{base_url}/api/generate'
    headers = _build_llm_headers(request_id=request_id)
    attempts = max(1, settings.LOCAL_LLM_RETRY_ATTEMPTS)
    model_errors: list[str] = []

    for model in _candidate_models():
        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json={
                        'model': model,
                        'prompt': prompt,
                        'stream': False,
                        'options': {'temperature': settings.LOCAL_LLM_TEMPERATURE},
                    },
                    timeout=settings.LOCAL_LLM_TIMEOUT_SECONDS,
                )
            except requests.RequestException as exc:
                error_msg = f'Falha de conexão no attempt {attempt}/{attempts} com modelo {model}.'
                model_errors.append(error_msg)
                logger.warning(
                    'local_llm_request_exception request_id=%s model=%s attempt=%s/%s error=%s',
                    request_id,
                    model,
                    attempt,
                    attempts,
                    exc,
                )
                if attempt < attempts:
                    time.sleep(settings.LOCAL_LLM_RETRY_BACKOFF_SECONDS * attempt)
                    continue
                break

            if response.status_code >= 400:
                detail = ''
                try:
                    detail = (response.json() or {}).get('error', '')
                except ValueError:
                    detail = response.text or ''

                err = detail or f'HTTP {response.status_code}'
                model_errors.append(f'Modelo {model} attempt {attempt}/{attempts}: {err}')
                logger.warning(
                    'local_llm_http_error request_id=%s model=%s attempt=%s/%s status=%s detail=%s',
                    request_id,
                    model,
                    attempt,
                    attempts,
                    response.status_code,
                    err,
                )
                if attempt < attempts:
                    time.sleep(settings.LOCAL_LLM_RETRY_BACKOFF_SECONDS * attempt)
                    continue
                break

            payload = response.json()
            answer = payload.get('response')
            if answer:
                _CIRCUIT_FAILURES = 0
                _CIRCUIT_OPEN_UNTIL = 0.0
                return answer, model

            model_errors.append(f'Modelo {model} retornou payload sem campo response.')
            logger.warning(
                'local_llm_invalid_payload request_id=%s model=%s attempt=%s/%s',
                request_id,
                model,
                attempt,
                attempts,
            )
            if attempt < attempts:
                time.sleep(settings.LOCAL_LLM_RETRY_BACKOFF_SECONDS * attempt)

    _CIRCUIT_FAILURES += 1
    if _CIRCUIT_FAILURES >= settings.LOCAL_LLM_CIRCUIT_FAILURE_THRESHOLD:
        _CIRCUIT_OPEN_UNTIL = time.time() + settings.LOCAL_LLM_CIRCUIT_OPEN_SECONDS

    summary = '; '.join(model_errors) if model_errors else 'erro desconhecido'
    raise LocalLLMExecutionError(f'Provedor de LLM local retornou erro: {summary}')


def gerar_insights_turma_rag(
    *,
    turma: Turma,
    question: str,
    dias: int | None,
    top_k: int,
    request_id: str | None = None,
) -> dict[str, Any]:
    if not settings.LOCAL_LLM_ENABLED:
        raise LocalLLMConfigError('LOCAL_LLM_ENABLED está desativado.')

    if not settings.LOCAL_LLM_MODEL:
        raise LocalLLMConfigError('LOCAL_LLM_MODEL não configurado.')

    chunks = _build_rag_chunks(turma=turma, dias=dias, top_k=top_k)
    source_id = f'turma_dashboard:{turma.id}:{dias or "all"}'
    document = persist_knowledge_chunks(
        source_id=source_id,
        source_type=KnowledgeDocument.SourceType.DASHBOARD,
        title=f'RAG Dashboard da Turma {turma.nome}',
        turma=turma,
        chunks=chunks,
        metadata={
            'dias': dias,
            'chunk_count': len(chunks),
            'llm_model': settings.LOCAL_LLM_MODEL,
        },
    )
    prompt = _build_prompt(question=question, chunks=chunks)
    answer, used_model = _ollama_generate(prompt=prompt, request_id=request_id)

    logger.info(
        'local_llm_insights_success request_id=%s turma_id=%s source_id=%s model=%s chunks=%s',
        request_id,
        turma.id,
        source_id,
        used_model,
        len(chunks),
    )

    return {
        'provider': 'ollama',
        'model': used_model,
        'question': question,
        'answer': answer,
        'request_id': request_id,
        'knowledge_document_id': document.id,
        'knowledge_document_version': document.version,
        'context_chunks_used': len(chunks),
        'sources': [{'title': c.title, 'content': c.content} for c in chunks],
    }
