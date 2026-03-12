from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings
from django.db.models import Avg

from core.models import Aluno, Avaliacao, Nota, Turma
from core.serializers import TurmaDashboardSerializer


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


def _ollama_generate(*, prompt: str) -> str:
    base_url = settings.LOCAL_LLM_BASE_URL.rstrip('/')
    url = f'{base_url}/api/generate'

    try:
        response = requests.post(
            url,
            json={
                'model': settings.LOCAL_LLM_MODEL,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': settings.LOCAL_LLM_TEMPERATURE},
            },
            timeout=settings.LOCAL_LLM_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise LocalLLMExecutionError('Falha ao conectar no provedor de LLM local.') from exc

    if response.status_code >= 400:
        raise LocalLLMExecutionError('Provedor de LLM local retornou erro.')

    payload = response.json()
    answer = payload.get('response')
    if not answer:
        raise LocalLLMExecutionError('Resposta inválida do provedor de LLM local.')
    return answer


def gerar_insights_turma_rag(*, turma: Turma, question: str, dias: int | None, top_k: int) -> dict[str, Any]:
    if not settings.LOCAL_LLM_ENABLED:
        raise LocalLLMConfigError('LOCAL_LLM_ENABLED está desativado.')

    if not settings.LOCAL_LLM_MODEL:
        raise LocalLLMConfigError('LOCAL_LLM_MODEL não configurado.')

    chunks = _build_rag_chunks(turma=turma, dias=dias, top_k=top_k)
    prompt = _build_prompt(question=question, chunks=chunks)
    answer = _ollama_generate(prompt=prompt)

    return {
        'provider': 'ollama',
        'model': settings.LOCAL_LLM_MODEL,
        'question': question,
        'answer': answer,
        'context_chunks_used': len(chunks),
        'sources': [{'title': c.title, 'content': c.content} for c in chunks],
    }
