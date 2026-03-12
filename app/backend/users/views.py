from django.contrib.auth.models import Group, User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from config.api_errors import error_response


@api_view(['GET'])
@permission_classes([AllowAny])
def healthcheck(_request):
    return Response({'service': 'backend-users', 'status': 'ok'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response(
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'groups': list(user.groups.values_list('name', flat=True)),
        }
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_role(request):
    username = request.data.get('username')
    role = request.data.get('role')

    if not username or not role:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code='validation_error',
            message='Campos obrigatórios: username e role.',
            details={
                'username': ['Este campo é obrigatório.'] if not username else [],
                'role': ['Este campo é obrigatório.'] if not role else [],
            },
        )

    role = str(role).strip().lower()
    if role not in {'professor', 'coordenador'}:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code='validation_error',
            message='Role inválida. Use: professor ou coordenador.',
            details={'role': ['Valor inválido. Use professor ou coordenador.']},
        )

    user = User.objects.filter(username=username).first()
    if not user:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code='not_found',
            message='Usuário não encontrado.',
        )

    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)

    return Response(
        {
            'detail': 'Role atribuída com sucesso.',
            'username': user.username,
            'groups': list(user.groups.values_list('name', flat=True)),
        }
    )
