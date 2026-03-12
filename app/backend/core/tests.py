from django.contrib.auth.models import Group, User
from django.test import TestCase
from unittest.mock import patch
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
        self.assertEqual(response.data['error']['code'], 'not_authenticated')
        self.assertIn('message', response.data['error'])

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
        self.assertEqual(response.data['error']['code'], 'not_found')
        self.assertEqual(response.data['error']['message'], 'Aluno não encontrado.')

    def test_transfer_aluno_missing_id(self):
        """Test transferring without aluno_id."""
        response = self.client.post(
            f'/api/turmas/{self.turma2.id}/transferir_aluno/',
            {},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['message'], 'Campo obrigatório: aluno_id.')
        self.assertEqual(response.data['error']['details']['aluno_id'], ['Este campo é obrigatório.'])


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
        self.assertEqual(response.data['total_notas_lancadas'], 1)
        self.assertEqual(response.data['percentual_notas_lancadas'], 100.0)
        self.assertEqual(
            response.data['distribuicao_notas'],
            {'ate_5': 0, 'de_5_a_7': 0, 'de_7_a_9': 1, 'acima_9': 0},
        )
        self.assertEqual(response.data['media_por_tipo_avaliacao'], [{'tipo': 'mensal', 'media': 8.75}])
        self.assertEqual(response.data['serie_avaliacoes'][0]['titulo'], 'Prova 1')
        self.assertEqual(response.data['comparativo_turma']['posicao'], 1)
        self.assertEqual(response.data['comparativo_turma']['total_turmas'], 1)
        self.assertIsNone(response.data['recorte_periodo'])

    def test_dashboard_turma_sem_notas(self):
        """Test dashboard metrics when there are no notas for turma."""
        turma_sem_notas = Turma.objects.create(
            nome="8A",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit,
        )
        Aluno.objects.create(
            nome="Maria",
            matricula="2026-0002",
            turma=turma_sem_notas,
        )
        Avaliacao.objects.create(
            titulo="Prova sem nota",
            tipo="mensal",
            turma=turma_sem_notas,
            data_aplicacao="2026-03-11",
        )

        response = self.client.get(f'/api/dashboard/turma/{turma_sem_notas.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['media_geral'], 0.0)
        self.assertEqual(response.data['total_notas_lancadas'], 0)
        self.assertEqual(response.data['percentual_notas_lancadas'], 0.0)
        self.assertEqual(
            response.data['distribuicao_notas'],
            {'ate_5': 0, 'de_5_a_7': 0, 'de_7_a_9': 0, 'acima_9': 0},
        )
        self.assertEqual(response.data['media_por_tipo_avaliacao'], [{'tipo': 'mensal', 'media': 0.0}])

    def test_dashboard_turma_not_found(self):
        """Test dashboard with invalid turma_id."""
        response = self.client.get('/api/dashboard/turma/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error']['code'], 'not_found')
        self.assertEqual(response.data['error']['message'], 'Turma não encontrada.')

    def test_dashboard_turma_comparativo_e_serie_recente(self):
        """Test dashboard returns cohort comparison and recent evaluation series."""
        turma_coorte = Turma.objects.create(
            nome='7B',
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit,
        )
        aluno_coorte = Aluno.objects.create(nome='Pedro', matricula='2026-0003', turma=turma_coorte)
        avaliacao_coorte = Avaliacao.objects.create(
            titulo='Prova Coorte',
            tipo='mensal',
            turma=turma_coorte,
            data_aplicacao='2026-03-10',
        )
        Nota.objects.create(aluno=aluno_coorte, avaliacao=avaliacao_coorte, valor=Decimal('6.00'))

        avaliacao_antiga = Avaliacao.objects.create(
            titulo='Prova 0',
            tipo='trimestral',
            turma=self.turma,
            data_aplicacao='2026-03-01',
        )
        Nota.objects.create(aluno=self.aluno, avaliacao=avaliacao_antiga, valor=Decimal('7.00'))

        response = self.client.get(f'/api/dashboard/turma/{self.turma.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['serie_avaliacoes']), 2)
        self.assertEqual(response.data['serie_avaliacoes'][0]['titulo'], 'Prova 1')
        self.assertEqual(response.data['serie_avaliacoes'][1]['titulo'], 'Prova 0')
        self.assertEqual(response.data['comparativo_turma']['posicao'], 1)
        self.assertEqual(response.data['comparativo_turma']['total_turmas'], 2)
        self.assertEqual(response.data['comparativo_turma']['media_coorte'], 7.25)
        self.assertEqual(response.data['comparativo_turma']['diferenca_media'], Decimal('0.63'))

    def test_dashboard_turma_recorte_por_periodo(self):
        """Test dashboard applies period cut based on latest evaluation date."""
        avaliacao_antiga = Avaliacao.objects.create(
            titulo='Prova Antiga',
            tipo='trimestral',
            turma=self.turma,
            data_aplicacao='2026-02-20',
        )
        Nota.objects.create(aluno=self.aluno, avaliacao=avaliacao_antiga, valor=Decimal('5.00'))

        response = self.client.get(f'/api/dashboard/turma/{self.turma.id}/?dias=7')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recorte_periodo']['dias'], 7)
        self.assertEqual(str(response.data['recorte_periodo']['data_inicio']), '2026-03-04')
        self.assertEqual(str(response.data['recorte_periodo']['data_fim']), '2026-03-10')
        self.assertEqual(response.data['recorte_periodo']['total_avaliacoes_periodo'], 1)
        self.assertEqual(response.data['recorte_periodo']['total_notas_periodo'], 1)
        self.assertEqual(response.data['recorte_periodo']['media_periodo'], 8.75)

    def test_dashboard_turma_recorte_dias_invalido(self):
        """Test dashboard rejects invalid dias query param."""
        response = self.client.get(f'/api/dashboard/turma/{self.turma.id}/?dias=abc')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['details']['dias'], ['Informe um número inteiro positivo.'])


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
        self.coordenador = User.objects.create_user(username="coord", password="CoordenadorPassword123")
        professor_group, _ = Group.objects.get_or_create(name="professor")
        coordenador_group, _ = Group.objects.get_or_create(name="coordenador")
        self.professor.groups.add(professor_group)
        self.coordenador.groups.add(coordenador_group)

        self.aluno = Aluno.objects.create(nome="Aluno RBAC", matricula="RBAC-0001", turma=self.turma)
        self.avaliacao = Avaliacao.objects.create(
            titulo="Aval RBAC",
            tipo="mensal",
            turma=self.turma,
            data_aplicacao="2026-03-10",
            peso=Decimal("1.00"),
        )

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
        self.assertEqual(response.data['error']['code'], 'permission_denied')

    def test_dashboard_allows_professor(self):
        self._auth('prof', 'ProfessorPassword123')
        response = self.client.get(f'/api/dashboard/turma/{self.turma.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_disciplina_list_allows_regular_user(self):
        self._auth('regular', 'RegularPassword123')
        response = self.client.get('/api/disciplinas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_disciplina_create_denies_professor(self):
        self._auth('prof', 'ProfessorPassword123')
        response = self.client.post(
            '/api/disciplinas/',
            {'nome': 'Física', 'codigo': 'FIS-001'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_disciplina_create_allows_coordenador(self):
        self._auth('coord', 'CoordenadorPassword123')
        response = self.client.post(
            '/api/disciplinas/',
            {'nome': 'Química', 'codigo': 'QUI-001'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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

    def test_nota_create_denies_regular_user(self):
        self._auth('regular', 'RegularPassword123')
        payload = {
            'aluno': self.aluno.id,
            'avaliacao': self.avaliacao.id,
            'valor': '7.50',
        }
        response = self.client.post('/api/notas/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nota_create_allows_professor(self):
        self._auth('prof', 'ProfessorPassword123')
        payload = {
            'aluno': self.aluno.id,
            'avaliacao': self.avaliacao.id,
            'valor': '8.50',
        }
        response = self.client.post('/api/notas/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_transfer_aluno_denies_professor(self):
        self._auth('prof', 'ProfessorPassword123')
        turma_destino = Turma.objects.create(
            nome="7B",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit,
        )
        response = self.client.post(
            f'/api/turmas/{turma_destino.id}/transferir_aluno/',
            {'aluno_id': self.aluno.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_transfer_aluno_allows_coordenador(self):
        self._auth('coord', 'CoordenadorPassword123')
        turma_destino = Turma.objects.create(
            nome="7C",
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit,
        )
        response = self.client.post(
            f'/api/turmas/{turma_destino.id}/transferir_aluno/',
            {'aluno_id': self.aluno.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GoogleSheetsIntegrationTest(APITestCase):
    """Tests for exporting turma dashboard to Google Sheets."""

    def setUp(self):
        self.client = APIClient()
        self.professor = User.objects.create_user(
            username='prof_sheets',
            password='ProfessorPassword123',
        )
        group, _ = Group.objects.get_or_create(name='professor')
        self.professor.groups.add(group)

        self.regular = User.objects.create_user(
            username='regular_sheets',
            password='RegularPassword123',
        )

        self.disc = Disciplina.objects.create(nome='Matemática Sheets', codigo='MAT-SHEETS-001')
        self.unit = Unidade.objects.create(nome='Escola Sheets', cidade='SP', estado='SP')
        self.turma = Turma.objects.create(
            nome='7S',
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit,
        )
        self.aluno = Aluno.objects.create(nome='Aluno Sheets', matricula='SHEETS-0001', turma=self.turma)
        self.aval = Avaliacao.objects.create(
            titulo='Prova Sheets',
            tipo='mensal',
            turma=self.turma,
            data_aplicacao='2026-03-10',
        )
        Nota.objects.create(aluno=self.aluno, avaliacao=self.aval, valor=Decimal('8.00'))

    def _auth(self, username: str, password: str):
        response = self.client.post(
            '/api/users/token/',
            {'username': username, 'password': password},
            format='json',
        )
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    @patch('core.views.export_dashboard_to_google_sheets')
    def test_export_dashboard_turma_google_sheets_success(self, export_mock):
        self._auth('prof_sheets', 'ProfessorPassword123')
        export_mock.return_value = {
            'spreadsheet_id': 'sheet-id-123',
            'worksheet': 'dashboard_turmas',
            'linhas_enviadas': 1,
        }

        response = self.client.post(
            f'/api/integrations/google-sheets/dashboard/turma/{self.turma.id}/export/',
            {'dias': 7},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['resultado']['spreadsheet_id'], 'sheet-id-123')
        self.assertEqual(response.data['resultado']['linhas_enviadas'], 1)
        export_mock.assert_called_once()

    def test_export_dashboard_turma_google_sheets_denies_regular_user(self):
        self._auth('regular_sheets', 'RegularPassword123')
        response = self.client.post(
            f'/api/integrations/google-sheets/dashboard/turma/{self.turma.id}/export/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error']['code'], 'permission_denied')

    def test_export_dashboard_turma_google_sheets_dias_invalido(self):
        self._auth('prof_sheets', 'ProfessorPassword123')
        response = self.client.post(
            f'/api/integrations/google-sheets/dashboard/turma/{self.turma.id}/export/',
            {'dias': 'abc'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['details']['dias'], ['Informe um número inteiro positivo.'])

    @patch('core.views.export_dashboard_to_google_sheets')
    def test_export_dashboard_turma_google_sheets_not_configured(self, export_mock):
        from core.integrations.google_sheets import GoogleSheetsConfigError

        self._auth('prof_sheets', 'ProfessorPassword123')
        export_mock.side_effect = GoogleSheetsConfigError('GOOGLE_SHEETS_CREDENTIALS_FILE não configurado.')

        response = self.client.post(
            f'/api/integrations/google-sheets/dashboard/turma/{self.turma.id}/export/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['error']['code'], 'integration_not_configured')


class LocalLLMRagIntegrationTest(APITestCase):
    """Tests for turma insights with self-hosted LLM + RAG."""

    def setUp(self):
        self.client = APIClient()
        self.professor = User.objects.create_user(
            username='prof_llm',
            password='ProfessorPassword123',
        )
        group, _ = Group.objects.get_or_create(name='professor')
        self.professor.groups.add(group)

        self.regular = User.objects.create_user(
            username='regular_llm',
            password='RegularPassword123',
        )

        self.disc = Disciplina.objects.create(nome='Ciências LLM', codigo='CIE-LLM-001')
        self.unit = Unidade.objects.create(nome='Escola LLM', cidade='SP', estado='SP')
        self.turma = Turma.objects.create(
            nome='8L',
            ano_letivo=2026,
            disciplina=self.disc,
            unidade=self.unit,
        )
        self.aluno = Aluno.objects.create(nome='Aluno LLM', matricula='LLM-0001', turma=self.turma)
        self.aval = Avaliacao.objects.create(
            titulo='Prova LLM',
            tipo='mensal',
            turma=self.turma,
            data_aplicacao='2026-03-11',
        )
        Nota.objects.create(aluno=self.aluno, avaliacao=self.aval, valor=Decimal('7.50'))

    def _auth(self, username: str, password: str):
        response = self.client.post(
            '/api/users/token/',
            {'username': username, 'password': password},
            format='json',
        )
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    @patch('core.views.gerar_insights_turma_rag')
    def test_gerar_insights_turma_llm_rag_success(self, rag_mock):
        self._auth('prof_llm', 'ProfessorPassword123')
        rag_mock.return_value = {
            'provider': 'ollama',
            'model': 'qwen2.5:7b-instruct',
            'question': 'Quais ações imediatas devo priorizar?',
            'answer': 'Diagnóstico e recomendações geradas.',
            'context_chunks_used': 4,
            'sources': [{'title': 'Resumo da turma', 'content': '...'}],
        }

        response = self.client.post(
            f'/api/integrations/llm-rag/dashboard/turma/{self.turma.id}/insights/',
            {
                'pergunta': 'Quais ações imediatas devo priorizar?',
                'dias': 14,
                'top_k': 5,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['resultado']['provider'], 'ollama')
        self.assertEqual(response.data['resultado']['context_chunks_used'], 4)
        rag_mock.assert_called_once()

    def test_gerar_insights_turma_llm_rag_denies_regular_user(self):
        self._auth('regular_llm', 'RegularPassword123')
        response = self.client.post(
            f'/api/integrations/llm-rag/dashboard/turma/{self.turma.id}/insights/',
            {'pergunta': 'Teste'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error']['code'], 'permission_denied')

    def test_gerar_insights_turma_llm_rag_validates_required_pergunta(self):
        self._auth('prof_llm', 'ProfessorPassword123')
        response = self.client.post(
            f'/api/integrations/llm-rag/dashboard/turma/{self.turma.id}/insights/',
            {'pergunta': '   '},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['details']['pergunta'], ['Este campo é obrigatório.'])

    def test_gerar_insights_turma_llm_rag_validates_top_k(self):
        self._auth('prof_llm', 'ProfessorPassword123')
        response = self.client.post(
            f'/api/integrations/llm-rag/dashboard/turma/{self.turma.id}/insights/',
            {'pergunta': 'Teste', 'top_k': 99},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['details']['top_k'], ['Informe um número inteiro entre 1 e 20.'])

    @patch('core.views.gerar_insights_turma_rag')
    def test_gerar_insights_turma_llm_rag_not_configured(self, rag_mock):
        from core.integrations.local_llm_rag import LocalLLMConfigError

        self._auth('prof_llm', 'ProfessorPassword123')
        rag_mock.side_effect = LocalLLMConfigError('LOCAL_LLM_ENABLED está desativado.')

        response = self.client.post(
            f'/api/integrations/llm-rag/dashboard/turma/{self.turma.id}/insights/',
            {'pergunta': 'Teste'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['error']['code'], 'integration_not_configured')

    @patch('core.views.gerar_insights_turma_rag')
    def test_gerar_insights_turma_llm_rag_provider_failure(self, rag_mock):
        from core.integrations.local_llm_rag import LocalLLMExecutionError

        self._auth('prof_llm', 'ProfessorPassword123')
        rag_mock.side_effect = LocalLLMExecutionError('Falha ao conectar no provedor de LLM local.')

        response = self.client.post(
            f'/api/integrations/llm-rag/dashboard/turma/{self.turma.id}/insights/',
            {'pergunta': 'Teste'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data['error']['code'], 'integration_error')
