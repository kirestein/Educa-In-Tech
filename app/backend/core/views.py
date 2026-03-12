from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from config.api_errors import error_response
from .integrations.google_sheets import (
    GoogleSheetsConfigError,
    GoogleSheetsSyncError,
    export_dashboard_to_google_sheets,
)
from .integrations.local_llm_rag import LocalLLMConfigError, LocalLLMExecutionError, gerar_insights_turma_rag
from .models import Aluno, Avaliacao, Disciplina, Nota, Turma, Unidade
from .permissions import IsAdminOrCoordinatorWrite, IsProfessorOrHigher, IsProfessorOrHigherWrite
from .serializers import (
    AlunoSerializer,
    AvaliacaoSerializer,
    DisciplinaSerializer,
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
