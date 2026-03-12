from django.contrib.auth.models import Group, User
from rest_framework.test import APITestCase
from rest_framework import status


class UserAuthenticationTest(APITestCase):
    """Tests for user authentication endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123",
            email="test@example.com"
        )

    def test_token_obtain_valid_credentials(self):
        """Test obtaining token with valid credentials."""
        response = self.client.post(
            '/api/users/token/',
            {
                'username': 'testuser',
                'password': 'TestPassword123'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_obtain_invalid_credentials(self):
        """Test token obtain with invalid credentials."""
        response = self.client.post(
            '/api/users/token/',
            {
                'username': 'testuser',
                'password': 'WrongPassword'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error']['code'], 'not_authenticated')
        self.assertIn('message', response.data['error'])

    def test_token_refresh(self):
        """Test refreshing access token."""
        login_response = self.client.post(
            '/api/users/token/',
            {
                'username': 'testuser',
                'password': 'TestPassword123'
            },
            format='json'
        )
        refresh_token = login_response.data['refresh']

        response = self.client.post(
            '/api/users/token/refresh/',
            {'refresh': refresh_token},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class UserMeEndpointTest(APITestCase):
    """Tests for /api/users/me/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123",
            email="test@example.com"
        )
        group, _ = Group.objects.get_or_create(name="professor")
        self.user.groups.add(group)

    def test_me_requires_authentication(self):
        """Test that /me endpoint requires authentication."""
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error']['code'], 'not_authenticated')

    def test_me_authenticated(self):
        """Test /me endpoint with valid token."""
        login_response = self.client.post(
            '/api/users/token/',
            {
                'username': 'testuser',
                'password': 'TestPassword123'
            },
            format='json'
        )
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('professor', response.data['groups'])


class RoleAssignmentTest(APITestCase):
    """Tests for role assignment endpoint."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="AdminPassword123",
            email="admin@example.com"
        )
        self.regular_user = User.objects.create_user(
            username="regular",
            password="RegularPassword123",
            email="regular@example.com"
        )

    def test_assign_role_requires_admin(self):
        """Test that role assignment requires admin privilege."""
        login_response = self.client.post(
            '/api/users/token/',
            {
                'username': 'regular',
                'password': 'RegularPassword123'
            },
            format='json'
        )
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post(
            '/api/users/roles/assign/',
            {
                'username': 'regular',
                'role': 'professor'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error']['code'], 'permission_denied')

    def test_assign_role_as_admin(self):
        """Test assigning role as admin."""
        login_response = self.client.post(
            '/api/users/token/',
            {
                'username': 'admin',
                'password': 'AdminPassword123'
            },
            format='json'
        )
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post(
            '/api/users/roles/assign/',
            {
                'username': 'regular',
                'role': 'professor'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('professor', response.data['groups'])

    def test_assign_invalid_role(self):
        """Test assigning invalid role."""
        login_response = self.client.post(
            '/api/users/token/',
            {
                'username': 'admin',
                'password': 'AdminPassword123'
            },
            format='json'
        )
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post(
            '/api/users/roles/assign/',
            {
                'username': 'regular',
                'role': 'invalid_role'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['details']['role'], ['Valor inválido. Use professor ou coordenador.'])

    def test_assign_role_nonexistent_user(self):
        """Test assigning role to non-existent user."""
        login_response = self.client.post(
            '/api/users/token/',
            {
                'username': 'admin',
                'password': 'AdminPassword123'
            },
            format='json'
        )
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post(
            '/api/users/roles/assign/',
            {
                'username': 'nonexistent',
                'role': 'professor'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error']['code'], 'not_found')
        self.assertEqual(response.data['error']['message'], 'Usuário não encontrado.')

    def test_assign_role_missing_fields(self):
        """Test assigning role without required fields."""
        login_response = self.client.post(
            '/api/users/token/',
            {
                'username': 'admin',
                'password': 'AdminPassword123'
            },
            format='json'
        )
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post('/api/users/roles/assign/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['details']['username'], ['Este campo é obrigatório.'])
        self.assertEqual(response.data['error']['details']['role'], ['Este campo é obrigatório.'])
