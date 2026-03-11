from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Aluno, Avaliacao, Disciplina, Nota, Turma, Unidade
from .permissions import IsAdminOrCoordinatorWrite, IsProfessorOrHigherWrite
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
def healthcheck(_request):
    return Response({'service': 'backend-core', 'status': 'ok'})


healthcheck.permission_classes = [AllowAny]


class DisciplinaViewSet(viewsets.ModelViewSet):
    queryset = Disciplina.objects.all()
    serializer_class = DisciplinaSerializer
    permission_classes = [IsAdminOrCoordinatorWrite]


class UnidadeViewSet(viewsets.ModelViewSet):
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer
    permission_classes = [IsAdminOrCoordinatorWrite]


class TurmaViewSet(viewsets.ModelViewSet):
    queryset = Turma.objects.select_related('disciplina', 'unidade').all()
    serializer_class = TurmaSerializer
    permission_classes = [IsAdminOrCoordinatorWrite]

    @action(detail=True, methods=['post'])
    def transferir_aluno(self, request, pk=None):
        turma_destino = self.get_object()
        aluno_id = request.data.get('aluno_id')
        aluno = get_object_or_404(Aluno, id=aluno_id)
        aluno.turma = turma_destino
        aluno.save(update_fields=['turma'])
        return Response({'detail': 'Aluno transferido com sucesso.'}, status=status.HTTP_200_OK)


class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.select_related('turma').all()
    serializer_class = AlunoSerializer
    permission_classes = [IsAdminOrCoordinatorWrite]


class AvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = Avaliacao.objects.select_related('turma').all()
    serializer_class = AvaliacaoSerializer
    permission_classes = [IsProfessorOrHigherWrite]


class NotaViewSet(viewsets.ModelViewSet):
    queryset = Nota.objects.select_related('aluno', 'avaliacao').all()
    serializer_class = NotaSerializer
    permission_classes = [IsProfessorOrHigherWrite]


@api_view(['GET'])
def dashboard_turma(_request, pk: int):
    turma = get_object_or_404(Turma, id=pk)
    serializer = TurmaDashboardSerializer(data=TurmaDashboardSerializer.build(turma))
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)
