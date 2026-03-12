from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from decimal import Decimal

from core.models import Aluno, Avaliacao, Disciplina, Nota, Turma, Unidade


class DisciplinaModelTest(TestCase):
    """Tests for Disciplina model."""

    def test_create_disciplina(self):
        """Test creating a disciplina."""
        disc = Disciplina.objects.create(
            nome="Matemática",
            codigo="MAT-001"
        )
        self.assertEqual(disc.nome, "Matemática")
        self.assertEqual(disc.codigo, "MAT-001")
        self.assertEqual(str(disc), "Matemática")

    def test_disciplina_nome_unique(self):
        """Test that disciplina nome is unique."""
        Disciplina.objects.create(nome="Português", codigo="PORT-001")
        with self.assertRaises(Exception):
            Disciplina.objects.create(nome="Português", codigo="PORT-002")

    def test_disciplina_codigo_unique(self):
        """Test that disciplina codigo is unique."""
        Disciplina.objects.create(nome="História", codigo="HIST-001")
        with self.assertRaises(Exception):
            Disciplina.objects.create(nome="História 2", codigo="HIST-001")


class UnidadeModelTest(TestCase):
    """Tests for Unidade model."""

    def test_create_unidade(self):
        """Test creating a unidade."""
        unit = Unidade.objects.create(
            nome="Escola Central",
            cidade="São Paulo",
            estado="SP"
        )
        self.assertEqual(unit.nome, "Escola Central")
        self.assertEqual(unit.cidade, "São Paulo")
        self.assertEqual(str(unit), "Escola Central")

    def test_unidade_unique_constraint(self):
        """Test unidade unique constraint on (nome, cidade, estado)."""
        Unidade.objects.create(nome="Escola A", cidade="São Paulo", estado="SP")
        with self.assertRaises(Exception):
            Unidade.objects.create(nome="Escola A", cidade="São Paulo", estado="SP")


class TurmaModelTest(TestCase):
    """Tests for Turma model."""

    def setUp(self):
        self.disc = Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        self.unit = Unidade.objects.create(nome="Escola 1", cidade="SP", estado="SP")

    def test_create_turma(self):
        """Test creating a turma."""
        turma = Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )
        self.assertEqual(turma.nome, "7A")
        self.assertEqual(turma.ano_letivo, 2026)
        self.assertEqual(str(turma), "7A (2026)")

    def test_turma_unique_constraint(self):
        """Test turma unique constraint on (nome, ano_letivo, disciplina, unidade)."""
        Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )
        with self.assertRaises(Exception):
            Turma.objects.create(
                nome="7A",
                ano_letivo=2026,
                disciplina=self.disc,
                unidade=self.unit
            )


class AlunoModelTest(TestCase):
    """Tests for Aluno model."""

    def setUp(self):
        self.disc = Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        self.unit = Unidade.objects.create(nome="Escola 1", cidade="SP", estado="SP")
        self.turma = Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )

    def test_create_aluno(self):
        """Test creating an aluno."""
        aluno = Aluno.objects.create(
            nome="João Silva",
            matricula="2026-0001",
            email="joao@example.com",
            turma=self.turma,
            ativo=True
        )
        self.assertEqual(aluno.nome, "João Silva")
        self.assertEqual(aluno.matricula, "2026-0001")
        self.assertTrue(aluno.ativo)

    def test_aluno_matricula_unique(self):
        """Test that aluno matricula is unique."""
        Aluno.objects.create(
            nome="Ana",
            matricula="2026-0001",
            turma=self.turma
        )
        with self.assertRaises(Exception):
            Aluno.objects.create(
                nome="Outro",
                matricula="2026-0001",
                turma=self.turma
            )


class AvaliacaoModelTest(TestCase):
    """Tests for Avaliacao model."""

    def setUp(self):
        self.disc = Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        self.unit = Unidade.objects.create(nome="Escola 1", cidade="SP", estado="SP")
        self.turma = Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )

    def test_create_avaliacao(self):
        """Test creating an avaliacao."""
        aval = Avaliacao.objects.create(
            titulo="Prova 1",
            tipo="mensal",
            turma=self.turma,
            peso=Decimal("2.00"),
            data_aplicacao="2026-03-10"
        )
        self.assertEqual(aval.titulo, "Prova 1")
        self.assertEqual(aval.tipo, "mensal")
        self.assertEqual(aval.peso, Decimal("2.00"))

    def test_avaliacao_tipos_choices(self):
        """Test avaliacao tipo choices."""
        tipos_validos = ["mensal", "trimestral", "formativa", "oral"]
        for tipo in tipos_validos:
            aval = Avaliacao.objects.create(
                titulo=f"Aval {tipo}",
                tipo=tipo,
                turma=self.turma,
                data_aplicacao="2026-03-10"
            )
            self.assertEqual(aval.tipo, tipo)


class NotaModelTest(TestCase):
    """Tests for Nota model."""

    def setUp(self):
        self.disc = Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        self.unit = Unidade.objects.create(nome="Escola 1", cidade="SP", estado="SP")
        self.turma = Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )
        self.aluno = Aluno.objects.create(
            nome="João",
            matricula="2026-0001",
            turma=self.turma
        )
        self.aval = Avaliacao.objects.create(
            titulo="Prova 1",
            tipo="mensal",
            turma=self.turma,
            data_aplicacao="2026-03-10"
        )

    def test_create_nota(self):
        """Test creating a nota."""
        nota = Nota.objects.create(
            aluno=self.aluno,
            avaliacao=self.aval,
            valor=Decimal("8.75"),
            entregue_em="2026-03-11"
        )
        self.assertEqual(nota.valor, Decimal("8.75"))

    def test_nota_unique_constraint(self):
        """Test nota unique constraint on (aluno, avaliacao)."""
        Nota.objects.create(
            aluno=self.aluno,
            avaliacao=self.aval,
            valor=Decimal("8.75")
        )
        with self.assertRaises(Exception):
            Nota.objects.create(
                aluno=self.aluno,
                avaliacao=self.aval,
                valor=Decimal("9.00")
            )


class APIAuthenticationTest(APITestCase):
    """Tests for API authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123",
            email="test@example.com"
        )
        group, _ = Group.objects.get_or_create(name="professor")
        self.user.groups.add(group)

    def test_token_obtain(self):
        """Test obtaining JWT token."""
        response = self.client.post(
            '/api/users/token/',
            {'username': 'testuser', 'password': 'TestPassword123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication."""
        response = self.client.get('/api/disciplinas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_with_token(self):
        """Test API call with valid token."""
        token_response = self.client.post(
            '/api/users/token/',
            {'username': 'testuser', 'password': 'TestPassword123'},
            format='json'
        )
        token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/disciplinas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DisciplinaAPITest(APITestCase):
    """Tests for Disciplina API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123",
            is_staff=True,
        )
        token_response = self.client.post(
            '/api/users/token/',
            {'username': 'testuser', 'password': 'TestPassword123'},
            format='json'
        )
        self.token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_disciplinas(self):
        """Test listing disciplinas."""
        Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        response = self.client.get('/api/disciplinas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_disciplina(self):
        """Test creating a disciplina via API."""
        data = {'nome': 'Português', 'codigo': 'PORT-001'}
        response = self.client.post('/api/disciplinas/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['nome'], 'Português')

    def test_retrieve_disciplina(self):
        """Test retrieving a disciplina."""
        disc = Disciplina.objects.create(nome="História", codigo="HIST-001")
        response = self.client.get(f'/api/disciplinas/{disc.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'História')

    def test_update_disciplina(self):
        """Test updating a disciplina."""
        disc = Disciplina.objects.create(nome="Ciências", codigo="CIEN-001")
        data = {'nome': 'Ciências Naturais', 'codigo': 'CIEN-001'}
        response = self.client.put(f'/api/disciplinas/{disc.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Ciências Naturais')

    def test_delete_disciplina(self):
        """Test deleting a disciplina."""
        disc = Disciplina.objects.create(nome="Educação Física", codigo="ED-001")
        response = self.client.delete(f'/api/disciplinas/{disc.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Disciplina.objects.filter(id=disc.id).exists())


class TurmaTransferAluno(APITestCase):
    """Tests for transferring aluno between turmas."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123",
            is_staff=True,
        )
        token_response = self.client.post(
            '/api/users/token/',
            {'username': 'testuser', 'password': 'TestPassword123'},
            format='json'
        )
        self.token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.disc = Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        self.unit = Unidade.objects.create(nome="Escola 1", cidade="SP", estado="SP")
        self.turma1 = Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )
        self.turma2 = Turma.objects.create(
            nome="7B",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )
        self.aluno = Aluno.objects.create(
            nome="João",
            matricula="2026-0001",
            turma=self.turma1
        )

    def test_transfer_aluno(self):
        """Test transferring aluno to another turma."""
        data = {'aluno_id': self.aluno.id}
        response = self.client.post(
            f'/api/turmas/{self.turma2.id}/transferir_aluno/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.turma.id, self.turma2.id)

    def test_transfer_aluno_invalid_id(self):
        """Test transferring with invalid aluno_id."""
        data = {'aluno_id': 99999}
        response = self.client.post(
            f'/api/turmas/{self.turma2.id}/transferir_aluno/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DashboardTurmaTest(APITestCase):
    """Tests for turma dashboard endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123"
        )
        group, _ = Group.objects.get_or_create(name="professor")
        self.user.groups.add(group)
        token_response = self.client.post(
            '/api/users/token/',
            {'username': 'testuser', 'password': 'TestPassword123'},
            format='json'
        )
        self.token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.disc = Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        self.unit = Unidade.objects.create(nome="Escola 1", cidade="SP", estado="SP")
        self.turma = Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit
        )
        self.aluno = Aluno.objects.create(
            nome="João",
            matricula="2026-0001",
            turma=self.turma
        )
        self.aval = Avaliacao.objects.create(
            titulo="Prova 1",
            tipo="mensal",
            turma=self.turma,
            data_aplicacao="2026-03-10"
        )
        Nota.objects.create(
            aluno=self.aluno,
            avaliacao=self.aval,
            valor=Decimal("8.75")
        )

    def test_dashboard_turma(self):
        """Test dashboard endpoint returns correct metrics."""
        response = self.client.get(f'/api/dashboard/turma/{self.turma.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['turma_id'], self.turma.id)
        self.assertEqual(response.data['total_alunos'], 1)
        self.assertEqual(response.data['total_avaliacoes'], 1)
        self.assertEqual(response.data['media_geral'], 8.75)

    def test_dashboard_turma_not_found(self):
        """Test dashboard with invalid turma_id."""
        response = self.client.get('/api/dashboard/turma/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RBACCoreAccessTest(APITestCase):
    """RBAC checks for core endpoints by role."""

    def setUp(self):
        self.disc = Disciplina.objects.create(nome="Matemática", codigo="MAT-001")
        self.unit = Unidade.objects.create(nome="Escola 1", cidade="SP", estado="SP")
        self.turma = Turma.objects.create(
            nome="7A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit,
        )

        self.regular = User.objects.create_user(username="regular", password="RegularPassword123")
        self.professor = User.objects.create_user(username="prof", password="ProfessorPassword123")
        professor_group, _ = Group.objects.get_or_create(name="professor")
        self.professor.groups.add(professor_group)

    def _auth(self, username: str, password: str):
        response = self.client.post(
            '/api/users/token/',
            {'username': username, 'password': password},
            format='json',
        )
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_dashboard_denies_regular_user(self):
        self._auth('regular', 'RegularPassword123')
        response = self.client.get(f'/api/dashboard/turma/{self.turma.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_allows_professor(self):
        self._auth('prof', 'ProfessorPassword123')
        response = self.client.get(f'/api/dashboard/turma/{self.turma.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_avaliacao_create_denies_regular_user(self):
        self._auth('regular', 'RegularPassword123')
        payload = {
            'titulo': 'Teste RBAC',
            'tipo': 'mensal',
            'turma': self.turma.id,
            'data_aplicacao': '2026-03-10',
            'peso': '1.00',
        }
        response = self.client.post('/api/avaliacoes/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_avaliacao_create_allows_professor(self):
        self._auth('prof', 'ProfessorPassword123')
        payload = {
            'titulo': 'Teste RBAC',
            'tipo': 'mensal',
            'turma': self.turma.id,
            'data_aplicacao': '2026-03-10',
            'peso': '1.00',
        }
        response = self.client.post('/api/avaliacoes/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
