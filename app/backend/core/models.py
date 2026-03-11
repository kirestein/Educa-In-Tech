from django.db import models


class Disciplina(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    codigo = models.CharField(max_length=30, unique=True, blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Unidade(models.Model):
    nome = models.CharField(max_length=150)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["nome", "cidade", "estado"],
                name="uniq_unidade_local",
            )
        ]

    def __str__(self):
        return self.nome


class Turma(models.Model):
    nome = models.CharField(max_length=120)
    ano_letivo = models.PositiveIntegerField()
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, related_name="turmas")
    unidade = models.ForeignKey(Unidade, on_delete=models.PROTECT, related_name="turmas")

    class Meta:
        ordering = ["-ano_letivo", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["nome", "ano_letivo", "disciplina", "unidade"],
                name="uniq_turma_contexto",
            )
        ]

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"


class Aluno(models.Model):
    nome = models.CharField(max_length=180)
    matricula = models.CharField(max_length=40, unique=True)
    email = models.EmailField(blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name="alunos")
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Avaliacao(models.Model):
    class Tipo(models.TextChoices):
        MENSAL = "mensal", "Mensal"
        TRIMESTRAL = "trimestral", "Trimestral"
        FORMATIVA = "formativa", "Formativa"
        ORAL = "oral", "Oral"

    titulo = models.CharField(max_length=160)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="avaliacoes")
    peso = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    data_aplicacao = models.DateField()
    prazo_entrega = models.DateField(null=True, blank=True)
    penalidade_atraso = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["-data_aplicacao", "titulo"]

    def __str__(self):
        return self.titulo


class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="notas")
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name="notas")
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    entregue_em = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["aluno__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["aluno", "avaliacao"],
                name="uniq_nota_aluno_avaliacao",
            )
        ]

    def __str__(self):
        return f"{self.aluno} - {self.avaliacao}: {self.valor}"
