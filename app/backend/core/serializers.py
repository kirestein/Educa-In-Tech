from django.db.models import Avg, Count
from rest_framework import serializers

from .models import Aluno, Avaliacao, Disciplina, Nota, Turma, Unidade


class DisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disciplina
        fields = '__all__'
        read_only_fields = ('id',)


class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = '__all__'
        read_only_fields = ('id',)


class TurmaSerializer(serializers.ModelSerializer):
    total_alunos = serializers.IntegerField(source='alunos.count', read_only=True)

    class Meta:
        model = Turma
        fields = ['id', 'nome', 'ano_letivo', 'disciplina', 'unidade', 'total_alunos']
        read_only_fields = ('id', 'total_alunos')


class AlunoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = '__all__'
        read_only_fields = ('id',)


class AvaliacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avaliacao
        fields = '__all__'
        read_only_fields = ('id',)


class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = '__all__'
        read_only_fields = ('id',)


class TurmaDashboardSerializer(serializers.Serializer):
    turma_id = serializers.IntegerField()
    turma_nome = serializers.CharField()
    media_geral = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_alunos = serializers.IntegerField()
    total_avaliacoes = serializers.IntegerField()

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return {**instance, **validated_data}

    @staticmethod
    def build(turma: Turma) -> dict:
        notas_agg = Nota.objects.filter(avaliacao__turma=turma).aggregate(media_geral=Avg('valor'))
        stats = {
            'turma_id': turma.id,
            'turma_nome': turma.nome,
            'media_geral': round(notas_agg['media_geral'] or 0, 2),
            'total_alunos': turma.alunos.aggregate(total=Count('id'))['total'],
            'total_avaliacoes': turma.avaliacoes.aggregate(total=Count('id'))['total'],
        }
        return stats