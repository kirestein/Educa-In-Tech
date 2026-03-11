from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AlunoViewSet,
    AvaliacaoViewSet,
    DisciplinaViewSet,
    NotaViewSet,
    TurmaViewSet,
    UnidadeViewSet,
    dashboard_turma,
    healthcheck,
)

router = DefaultRouter()
router.register('disciplinas', DisciplinaViewSet, basename='disciplinas')
router.register('unidades', UnidadeViewSet, basename='unidades')
router.register('turmas', TurmaViewSet, basename='turmas')
router.register('alunos', AlunoViewSet, basename='alunos')
router.register('avaliacoes', AvaliacaoViewSet, basename='avaliacoes')
router.register('notas', NotaViewSet, basename='notas')

urlpatterns = [
    path('health/', healthcheck, name='core-healthcheck'),
    path('dashboard/turma/<int:pk>/', dashboard_turma, name='dashboard-turma'),
    path('', include(router.urls)),
]