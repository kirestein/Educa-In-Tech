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


class KnowledgeDocument(models.Model):
    class SourceType(models.TextChoices):
        DASHBOARD = 'dashboard', 'Dashboard'
        MANUAL = 'manual', 'Manual'
        FILE = 'file', 'Arquivo'

    source_id = models.CharField(max_length=190)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.MANUAL)
    title = models.CharField(max_length=180)
    version = models.PositiveIntegerField(default=1)
    checksum = models.CharField(max_length=64)
    turma = models.ForeignKey(
        Turma,
        on_delete=models.SET_NULL,
        related_name='knowledge_documents',
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['source_id', 'version'],
                name='uniq_kdoc_source_version',
            )
        ]
        indexes = [
            models.Index(fields=['source_id'], name='idx_knowledge_document_source'),
            models.Index(fields=['source_type', 'is_active'], name='idx_kdoc_type_active'),
        ]

    def __str__(self):
        return f"{self.source_id} v{self.version}"


class KnowledgeChunk(models.Model):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name='chunks')
    position = models.PositiveIntegerField()
    title = models.CharField(max_length=180)
    content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    embedding_model = models.CharField(max_length=120, blank=True)
    embedding_dim = models.PositiveIntegerField(null=True, blank=True)
    embedding_vector = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document_id', 'position']
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'position'],
                name='uniq_kchunk_doc_pos',
            )
        ]
        indexes = [
            models.Index(fields=['document', 'position'], name='idx_kchunk_doc_pos'),
        ]

    def __str__(self):
        return f"{self.document_id}#{self.position}"
