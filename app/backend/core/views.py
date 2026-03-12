from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from config.api_errors import error_response
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


@api_view(['GET'])
@permission_classes([IsProfessorOrHigher])
def dashboard_turma(_request, pk: int):
    turma = Turma.objects.filter(id=pk).first()
    if not turma:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code='not_found',
            message='Turma não encontrada.',
        )

    serializer = TurmaDashboardSerializer(data=TurmaDashboardSerializer.build(turma))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)
