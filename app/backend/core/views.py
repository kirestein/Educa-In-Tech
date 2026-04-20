from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
import re
import uuid

from config.api_errors import error_response
from .integrations.google_sheets import (
    GoogleSheetsConfigError,
    GoogleSheetsSyncError,
    export_dashboard_to_google_sheets,
)
from .integrations.local_llm_rag import (
    LocalLLMConfigError,
    LocalLLMExecutionError,
    RagChunk,
    gerar_insights_turma_rag,
    persist_knowledge_chunks,
)
from .models import Aluno, Avaliacao, Disciplina, KnowledgeChunk, KnowledgeDocument, Nota, Turma, Unidade
from .permissions import IsAdminOrCoordinatorWrite, IsProfessorOrHigher, IsProfessorOrHigherWrite
from .serializers import (
    AlunoSerializer,
    AvaliacaoSerializer,
    DisciplinaSerializer,
    KnowledgeChunkSerializer,
    KnowledgeDocumentSerializer,
    NotaSerializer,
    TurmaDashboardSerializer,
    TurmaSerializer,
    UnidadeSerializer,
)


@extend_schema(
    operation_id='core_healthcheck',
    responses={
        200: inline_serializer(
            name='CoreHealthcheckResponse',
            fields={
                'service': serializers.CharField(),
                'status': serializers.CharField(),
            },
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def healthcheck(_request):
    return Response({'service': 'backend-core', 'status': 'ok'})


class DisciplinaViewSet(viewsets.ModelViewSet):
    queryset = Disciplina.objects.all()
    serializer_class = DisciplinaSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAdminOrCoordinatorWrite()]


class UnidadeViewSet(viewsets.ModelViewSet):
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAdminOrCoordinatorWrite()]


class TurmaViewSet(viewsets.ModelViewSet):
    queryset = Turma.objects.select_related('disciplina', 'unidade').all()
    serializer_class = TurmaSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        if self.action == 'transferir_aluno':
            return [IsAdminOrCoordinatorWrite()]
        return [IsAdminOrCoordinatorWrite()]

    @action(detail=True, methods=['post'])
    @extend_schema(
        operation_id='turma_transferir_aluno',
        request=inline_serializer(
            name='TransferirAlunoRequest',
            fields={'aluno_id': serializers.IntegerField()},
        ),
        responses={
            200: inline_serializer(
                name='TransferirAlunoResponse',
                fields={'detail': serializers.CharField()},
            ),
            400: OpenApiResponse(description='Campo aluno_id obrigatório.'),
            404: OpenApiResponse(description='Aluno não encontrado.'),
        },
    )
    def transferir_aluno(self, request, pk=None):
        turma_destino = self.get_object()
        aluno_id = request.data.get('aluno_id')
        if not aluno_id:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Campo obrigatório: aluno_id.',
                details={'aluno_id': ['Este campo é obrigatório.']},
            )

        aluno = Aluno.objects.filter(id=aluno_id).first()
        if not aluno:
            return error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                code='not_found',
                message='Aluno não encontrado.',
            )

        aluno.turma = turma_destino
        aluno.save(update_fields=['turma'])
        return Response({'detail': 'Aluno transferido com sucesso.'}, status=status.HTTP_200_OK)


class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.select_related('turma').all()
    serializer_class = AlunoSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAdminOrCoordinatorWrite()]


class AvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = Avaliacao.objects.select_related('turma').all()
    serializer_class = AvaliacaoSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsProfessorOrHigherWrite()]


class NotaViewSet(viewsets.ModelViewSet):
    queryset = Nota.objects.select_related('aluno', 'avaliacao').all()
    serializer_class = NotaSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsProfessorOrHigherWrite()]


class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeDocument.objects.select_related('turma').prefetch_related('chunks').all()
    serializer_class = KnowledgeDocumentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        source_id = self.request.query_params.get('source_id')
        source_type = self.request.query_params.get('source_type')
        turma_id = self.request.query_params.get('turma_id')
        is_active = self.request.query_params.get('is_active')

        if source_id:
            queryset = queryset.filter(source_id=source_id)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        if turma_id:
            queryset = queryset.filter(turma_id=turma_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=str(is_active).lower() in {'1', 'true', 'yes'})

        return queryset

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAdminOrCoordinatorWrite()]

    @action(detail=False, methods=['post'], url_path='ingest-text')
    @extend_schema(
        operation_id='knowledge_ingest_text',
        request=inline_serializer(
            name='KnowledgeIngestTextRequest',
            fields={
                'source_id': serializers.CharField(),
                'source_type': serializers.ChoiceField(choices=KnowledgeDocument.SourceType.choices),
                'title': serializers.CharField(),
                'text': serializers.CharField(),
                'turma_id': serializers.IntegerField(required=False),
                'chunk_size': serializers.IntegerField(required=False),
            },
        ),
        responses={
            201: inline_serializer(
                name='KnowledgeIngestTextResponse',
                fields={
                    'detail': serializers.CharField(),
                    'knowledge_document_id': serializers.IntegerField(),
                    'knowledge_document_version': serializers.IntegerField(),
                    'chunks_created': serializers.IntegerField(),
                },
            ),
            400: OpenApiResponse(description='Payload inválido.'),
            404: OpenApiResponse(description='Turma não encontrada.'),
        },
    )
    def ingest_text(self, request):
        source_id = (request.data.get('source_id') or '').strip()
        source_type = (request.data.get('source_type') or '').strip()
        title = (request.data.get('title') or '').strip()
        text = (request.data.get('text') or '').strip()

        if not source_id or not source_type or not title or not text:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Campos obrigatórios: source_id, source_type, title e text.',
            )

        valid_types = {choice for choice, _ in KnowledgeDocument.SourceType.choices}
        if source_type not in valid_types:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='source_type inválido.',
                details={'source_type': [f'Valores permitidos: {", ".join(sorted(valid_types))}.']},
            )

        turma = None
        turma_id = request.data.get('turma_id')
        if turma_id is not None:
            turma = Turma.objects.filter(id=turma_id).first()
            if not turma:
                return error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code='not_found',
                    message='Turma não encontrada.',
                )

        chunk_size = request.data.get('chunk_size', 800)
        try:
            chunk_size = int(chunk_size)
        except (TypeError, ValueError):
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='chunk_size deve ser inteiro entre 200 e 4000.',
                details={'chunk_size': ['Informe um inteiro entre 200 e 4000.']},
            )

        if chunk_size < 200 or chunk_size > 4000:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='chunk_size deve ser inteiro entre 200 e 4000.',
                details={'chunk_size': ['Informe um inteiro entre 200 e 4000.']},
            )

        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        chunks: list[RagChunk] = []
        buffer = ''
        for paragraph in paragraphs:
            candidate = f'{buffer}\n\n{paragraph}'.strip() if buffer else paragraph
            if len(candidate) <= chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(RagChunk(title=title, content=buffer))
                buffer = paragraph
            else:
                # Hard-split for oversized paragraphs.
                for i in range(0, len(paragraph), chunk_size):
                    piece = paragraph[i : i + chunk_size].strip()
                    if piece:
                        chunks.append(RagChunk(title=title, content=piece))
                buffer = ''

        if buffer:
            chunks.append(RagChunk(title=title, content=buffer))

        document = persist_knowledge_chunks(
            source_id=source_id,
            source_type=source_type,
            title=title,
            turma=turma,
            chunks=chunks,
            metadata={
                'ingest_mode': 'manual_text',
                'chunk_size': chunk_size,
                'chunk_count': len(chunks),
            },
        )

        return Response(
            {
                'detail': 'Conhecimento ingerido com sucesso.',
                'knowledge_document_id': document.id,
                'knowledge_document_version': document.version,
                'chunks_created': len(chunks),
            },
            status=status.HTTP_201_CREATED,
        )


class KnowledgeChunkViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeChunk.objects.select_related('document').all()
    serializer_class = KnowledgeChunkSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        document_id = self.request.query_params.get('document_id')
        source_id = self.request.query_params.get('source_id')
        source_type = self.request.query_params.get('source_type')
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        if source_id:
            queryset = queryset.filter(document__source_id=source_id)
        if source_type:
            queryset = queryset.filter(document__source_type=source_type)
        return queryset

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAdminOrCoordinatorWrite()]

    @action(detail=False, methods=['get'], url_path='search')
    @extend_schema(
        operation_id='knowledge_search_chunks',
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Texto da busca. Usa ranking textual simples por ocorrência.',
            ),
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Limite de resultados (1-50, default 10).',
            ),
            OpenApiParameter(
                name='source_type',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filtro por tipo de fonte (dashboard/manual/file).',
            ),
            OpenApiParameter(
                name='turma_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filtro por turma associada ao documento.',
            ),
        ],
        responses={
            200: inline_serializer(
                name='KnowledgeSearchChunksResponse',
                fields={
                    'query': serializers.CharField(),
                    'total_matches': serializers.IntegerField(),
                    'results': inline_serializer(
                        name='KnowledgeSearchChunksResultItem',
                        many=True,
                        fields={
                            'chunk_id': serializers.IntegerField(),
                            'document_id': serializers.IntegerField(),
                            'source_id': serializers.CharField(),
                            'source_type': serializers.CharField(),
                            'turma_id': serializers.IntegerField(allow_null=True),
                            'title': serializers.CharField(),
                            'snippet': serializers.CharField(),
                            'score': serializers.IntegerField(),
                        },
                    ),
                },
            ),
            400: OpenApiResponse(description='Parâmetros inválidos.'),
        },
    )
    def search(self, request):
        query = (request.query_params.get('q') or '').strip()
        if not query:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro obrigatório: q.',
                details={'q': ['Informe um texto de busca.']},
            )

        limit_param = request.query_params.get('limit', 10)
        try:
            limit = int(limit_param)
        except (TypeError, ValueError):
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro limit deve ser inteiro entre 1 e 50.',
                details={'limit': ['Informe um inteiro entre 1 e 50.']},
            )

        if limit < 1 or limit > 50:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro limit deve ser inteiro entre 1 e 50.',
                details={'limit': ['Informe um inteiro entre 1 e 50.']},
            )

        queryset = KnowledgeChunk.objects.select_related('document', 'document__turma').filter(
            document__is_active=True
        )

        source_type = request.query_params.get('source_type')
        if source_type:
            queryset = queryset.filter(document__source_type=source_type)

        turma_id = request.query_params.get('turma_id')
        if turma_id:
            queryset = queryset.filter(document__turma_id=turma_id)

        tokens = [t for t in re.split(r'\W+', query.lower()) if len(t) >= 2]
        if not tokens:
            tokens = [query.lower()]

        # Local-first ranking: simple lexical relevance, no vector dependency.
        candidates = list(queryset[:1000])
        scored: list[tuple[int, KnowledgeChunk]] = []
        for chunk in candidates:
            content = chunk.content.lower()
            title = chunk.title.lower()
            score = 0
            for token in tokens:
                score += content.count(token)
                score += title.count(token) * 2
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1].id))
        results = []
        for score, chunk in scored[:limit]:
            snippet = chunk.content[:240]
            if len(chunk.content) > 240:
                snippet += '...'
            results.append(
                {
                    'chunk_id': chunk.id,
                    'document_id': chunk.document_id,
                    'source_id': chunk.document.source_id,
                    'source_type': chunk.document.source_type,
                    'turma_id': chunk.document.turma_id,
                    'title': chunk.title,
                    'snippet': snippet,
                    'score': score,
                }
            )

        return Response({'query': query, 'total_matches': len(scored), 'results': results})


@extend_schema(
    operation_id='dashboard_turma',
    parameters=[
        OpenApiParameter(
            name='dias',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Recorte opcional em dias, calculado a partir da avaliação mais recente da turma.',
        )
    ],
    responses={
        200: TurmaDashboardSerializer,
        400: OpenApiResponse(description='Parâmetro dias inválido.'),
        404: OpenApiResponse(description='Turma não encontrada.'),
    },
)
@api_view(['GET'])
@permission_classes([IsProfessorOrHigher])
def dashboard_turma(request, pk: int):
    turma = Turma.objects.filter(id=pk).first()
    if not turma:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code='not_found',
            message='Turma não encontrada.',
        )

    dias_param = request.query_params.get('dias')
    dias = None
    if dias_param is not None:
        try:
            dias = int(dias_param)
        except (TypeError, ValueError):
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro dias deve ser um inteiro positivo.',
                details={'dias': ['Informe um número inteiro positivo.']},
            )

        if dias <= 0:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro dias deve ser um inteiro positivo.',
                details={'dias': ['Informe um número inteiro positivo.']},
            )

    serializer = TurmaDashboardSerializer(data=TurmaDashboardSerializer.build(turma, dias=dias))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)


@extend_schema(
    operation_id='exportar_dashboard_turma_google_sheets',
    request=inline_serializer(
        name='ExportarDashboardGoogleSheetsRequest',
        fields={
            'dias': serializers.IntegerField(required=False),
            'spreadsheet_id': serializers.CharField(required=False),
            'worksheet': serializers.CharField(required=False),
        },
    ),
    responses={
        200: inline_serializer(
            name='ExportarDashboardGoogleSheetsResponse',
            fields={
                'detail': serializers.CharField(),
                'resultado': inline_serializer(
                    name='ExportarDashboardGoogleSheetsResult',
                    fields={
                        'spreadsheet_id': serializers.CharField(),
                        'worksheet': serializers.CharField(),
                        'linhas_enviadas': serializers.IntegerField(),
                    },
                ),
            },
        ),
        400: OpenApiResponse(description='Parâmetro dias inválido.'),
        404: OpenApiResponse(description='Turma não encontrada.'),
        503: OpenApiResponse(description='Integração com Google Sheets não configurada.'),
    },
)
@api_view(['POST'])
@permission_classes([IsProfessorOrHigher])
def exportar_dashboard_turma_google_sheets(request, pk: int):
    turma = Turma.objects.select_related('disciplina', 'unidade').filter(id=pk).first()
    if not turma:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code='not_found',
            message='Turma não encontrada.',
        )

    dias_param = request.data.get('dias')
    dias = None
    if dias_param is not None:
        try:
            dias = int(dias_param)
        except (TypeError, ValueError):
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro dias deve ser um inteiro positivo.',
                details={'dias': ['Informe um número inteiro positivo.']},
            )

        if dias <= 0:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro dias deve ser um inteiro positivo.',
                details={'dias': ['Informe um número inteiro positivo.']},
            )

    dashboard_data = TurmaDashboardSerializer.build(turma, dias=dias)

    try:
        result = export_dashboard_to_google_sheets(
            turma=turma,
            dashboard_data=dashboard_data,
            dias=dias,
            spreadsheet_id=request.data.get('spreadsheet_id'),
            worksheet_name=request.data.get('worksheet'),
        )
    except GoogleSheetsConfigError as exc:
        return error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code='integration_not_configured',
            message='Integração com Google Sheets não está configurada.',
            details={'google_sheets': [str(exc)]},
        )
    except GoogleSheetsSyncError as exc:
        return error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code='integration_error',
            message='Falha ao enviar dados para Google Sheets.',
            details={'google_sheets': [str(exc)]},
        )

    return Response(
        {
            'detail': 'Dashboard exportado com sucesso para Google Sheets.',
            'resultado': result,
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    operation_id='gerar_insights_turma_llm_rag',
    request=inline_serializer(
        name='GerarInsightsTurmaLLMRagRequest',
        fields={
            'pergunta': serializers.CharField(),
            'dias': serializers.IntegerField(required=False),
            'top_k': serializers.IntegerField(required=False),
        },
    ),
    responses={
        200: inline_serializer(
            name='GerarInsightsTurmaLLMRagResponse',
            fields={
                'detail': serializers.CharField(),
                'resultado': inline_serializer(
                    name='GerarInsightsTurmaLLMRagResult',
                    fields={
                        'provider': serializers.CharField(),
                        'model': serializers.CharField(),
                        'question': serializers.CharField(),
                        'answer': serializers.CharField(),
                        'request_id': serializers.CharField(allow_null=True),
                        'knowledge_document_id': serializers.IntegerField(),
                        'knowledge_document_version': serializers.IntegerField(),
                        'context_chunks_used': serializers.IntegerField(),
                        'sources': inline_serializer(
                            name='GerarInsightsTurmaLLMRagSource',
                            many=True,
                            fields={
                                'title': serializers.CharField(),
                                'content': serializers.CharField(),
                            },
                        ),
                    },
                ),
            },
        ),
        400: OpenApiResponse(description='Parâmetros inválidos.'),
        404: OpenApiResponse(description='Turma não encontrada.'),
        503: OpenApiResponse(description='LLM local não configurado.'),
    },
)
@api_view(['POST'])
@permission_classes([IsProfessorOrHigher])
def gerar_insights_turma_llm_rag(request, pk: int):
    request_id = request.headers.get('X-Request-Id') or str(uuid.uuid4())
    turma = Turma.objects.select_related('disciplina', 'unidade').filter(id=pk).first()
    if not turma:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code='not_found',
            message='Turma não encontrada.',
        )

    pergunta = (request.data.get('pergunta') or '').strip()
    if not pergunta:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code='validation_error',
            message='Campo obrigatório: pergunta.',
            details={'pergunta': ['Este campo é obrigatório.']},
        )

    dias = None
    dias_param = request.data.get('dias')
    if dias_param is not None:
        try:
            dias = int(dias_param)
        except (TypeError, ValueError):
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro dias deve ser um inteiro positivo.',
                details={'dias': ['Informe um número inteiro positivo.']},
            )

        if dias <= 0:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code='validation_error',
                message='Parâmetro dias deve ser um inteiro positivo.',
                details={'dias': ['Informe um número inteiro positivo.']},
            )

    top_k_param = request.data.get('top_k', 6)
    try:
        top_k = int(top_k_param)
    except (TypeError, ValueError):
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code='validation_error',
            message='Parâmetro top_k deve ser um inteiro entre 1 e 20.',
            details={'top_k': ['Informe um número inteiro entre 1 e 20.']},
        )

    if top_k <= 0 or top_k > 20:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code='validation_error',
            message='Parâmetro top_k deve ser um inteiro entre 1 e 20.',
            details={'top_k': ['Informe um número inteiro entre 1 e 20.']},
        )

    try:
        result = gerar_insights_turma_rag(
            turma=turma,
            question=pergunta,
            dias=dias,
            top_k=top_k,
            request_id=request_id,
        )
    except LocalLLMConfigError as exc:
        return error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code='integration_not_configured',
            message='Integração com LLM local não está configurada.',
            details={'llm_local': [str(exc)]},
        )
    except LocalLLMExecutionError as exc:
        return error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code='integration_error',
            message='Falha ao gerar insights com LLM local.',
            details={'llm_local': [str(exc)]},
        )

    return Response(
        {
            'detail': 'Insights gerados com sucesso via LLM local com RAG.',
            'resultado': result,
        },
        status=status.HTTP_200_OK,
    )
