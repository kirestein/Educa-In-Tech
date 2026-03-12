from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count, Q
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


class MediaPorTipoAvaliacaoSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    media = serializers.DecimalField(max_digits=10, decimal_places=2)


class DistribuicaoNotasSerializer(serializers.Serializer):
    ate_5 = serializers.IntegerField()
    de_5_a_7 = serializers.IntegerField()
    de_7_a_9 = serializers.IntegerField()
    acima_9 = serializers.IntegerField()


class TurmaDashboardSerializer(serializers.Serializer):
    turma_id = serializers.IntegerField()
    turma_nome = serializers.CharField()
    media_geral = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_alunos = serializers.IntegerField()
    total_avaliacoes = serializers.IntegerField()
    total_notas_lancadas = serializers.IntegerField()
    percentual_notas_lancadas = serializers.DecimalField(max_digits=5, decimal_places=2)
    distribuicao_notas = DistribuicaoNotasSerializer()
    media_por_tipo_avaliacao = MediaPorTipoAvaliacaoSerializer(many=True)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return {**instance, **validated_data}

    @staticmethod
    def _quantize(value) -> Decimal:
        if value is None:
            return Decimal('0.00')
        return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def build(turma: Turma) -> dict:
        notas_qs = Nota.objects.filter(avaliacao__turma=turma)
        notas_agg = notas_qs.aggregate(media_geral=Avg('valor'))
        total_alunos = turma.alunos.aggregate(total=Count('id'))['total']
        total_avaliacoes = turma.avaliacoes.aggregate(total=Count('id'))['total']
        total_notas_lancadas = notas_qs.aggregate(total=Count('id'))['total']

        capacidade_total = total_alunos * total_avaliacoes
        if capacidade_total > 0:
            percentual_notas_lancadas = (
                Decimal(total_notas_lancadas) * Decimal('100') / Decimal(capacidade_total)
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            percentual_notas_lancadas = Decimal('0.00')

        distribuicao_notas = notas_qs.aggregate(
            ate_5=Count('id', filter=Q(valor__lt=5)),
            de_5_a_7=Count('id', filter=Q(valor__gte=5, valor__lt=7)),
            de_7_a_9=Count('id', filter=Q(valor__gte=7, valor__lt=9)),
            acima_9=Count('id', filter=Q(valor__gte=9)),
        )

        media_por_tipo = (
            Avaliacao.objects.filter(turma=turma)
            .values('tipo')
            .annotate(media=Avg('notas__valor'))
            .order_by('tipo')
        )

        stats = {
            'turma_id': turma.id,
            'turma_nome': turma.nome,
            'media_geral': TurmaDashboardSerializer._quantize(notas_agg['media_geral']),
            'total_alunos': total_alunos,
            'total_avaliacoes': total_avaliacoes,
            'total_notas_lancadas': total_notas_lancadas,
            'percentual_notas_lancadas': percentual_notas_lancadas,
            'distribuicao_notas': distribuicao_notas,
            'media_por_tipo_avaliacao': [
                {
                    'tipo': row['tipo'],
                    'media': TurmaDashboardSerializer._quantize(row['media']),
                }
                for row in media_por_tipo
            ],
        }
        return stats