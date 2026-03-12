from rest_framework.permissions import SAFE_METHODS, BasePermission


ROLE_PROFESSOR = 'professor'
ROLE_COORDENADOR = 'coordenador'


def _is_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def _has_group(user, role_name: str) -> bool:
    return bool(user and user.is_authenticated and user.groups.filter(name=role_name).exists())


def _is_professor_or_higher(user) -> bool:
    return (
        _is_admin(user)
        or _has_group(user, ROLE_COORDENADOR)
        or _has_group(user, ROLE_PROFESSOR)
    )


class IsAdminOrCoordinatorWrite(BasePermission):
    """
    Leitura para qualquer usuário autenticado.
    Escrita apenas para admin/superuser/coordenador.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return _is_admin(user) or _has_group(user, ROLE_COORDENADOR)


class IsProfessorOrHigher(BasePermission):
    """
    Acesso para professor, coordenador e admin/superuser.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return _is_professor_or_higher(user)


class IsProfessorOrHigherWrite(BasePermission):
    """
    Leitura para qualquer usuário autenticado.
    Escrita para professor, coordenador e admin.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return _is_professor_or_higher(user)
