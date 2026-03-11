from django.contrib import admin

from .models import Aluno, Avaliacao, Disciplina, Nota, Turma, Unidade


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'codigo')
    search_fields = ('nome', 'codigo')


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'cidade', 'estado')
    search_fields = ('nome', 'cidade')


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'ano_letivo', 'disciplina', 'unidade')
    list_filter = ('ano_letivo', 'disciplina', 'unidade')
    search_fields = ('nome',)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'matricula', 'turma', 'ativo')
    list_filter = ('ativo', 'turma')
    search_fields = ('nome', 'matricula', 'email')


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'tipo', 'turma', 'peso', 'data_aplicacao')
    list_filter = ('tipo', 'turma')
    search_fields = ('titulo',)


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('id', 'aluno', 'avaliacao', 'valor', 'entregue_em')
    list_filter = ('avaliacao',)
