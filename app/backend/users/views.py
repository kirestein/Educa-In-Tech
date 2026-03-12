from django.contrib.auth.models import Group, User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response


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
        return Response(
            {'detail': 'Campos obrigatórios: username e role.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    role = str(role).strip().lower()
    if role not in {'professor', 'coordenador'}:
        return Response(
            {'detail': 'Role inválida. Use: professor ou coordenador.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(username=username).first()
    if not user:
        return Response({'detail': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)

    return Response(
        {
            'detail': 'Role atribuída com sucesso.',
            'username': user.username,
            'groups': list(user.groups.values_list('name', flat=True)),
        }
    )
