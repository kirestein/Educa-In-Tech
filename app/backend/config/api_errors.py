from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


DEFAULT_CLIENT_ERROR_MESSAGE = 'Erro na requisição.'
DEFAULT_SERVER_ERROR_MESSAGE = 'Erro interno do servidor.'


def _normalize_error_details(data: Any) -> Any:
    if isinstance(data, ErrorDetail):
        return str(data)
    if isinstance(data, list):
        return [_normalize_error_details(item) for item in data]
    if isinstance(data, dict):
        return {key: _normalize_error_details(value) for key, value in data.items()}
    return data


def build_error_payload(message: str, code: str, details: Any | None = None) -> dict[str, Any]:
    return {
        'error': {
            'code': code,
            'message': message,
            'details': details or {},
        }
    }


def error_response(status_code: int, code: str, message: str, details: Any | None = None) -> Response:
    return Response(build_error_payload(message=message, code=code, details=details), status=status_code)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    normalized_details = _normalize_error_details(response.data)
    message = DEFAULT_CLIENT_ERROR_MESSAGE if response.status_code < 500 else DEFAULT_SERVER_ERROR_MESSAGE
    code = getattr(exc, 'default_code', 'error')
    details: Any = {}

    if isinstance(exc, ValidationError):
        message = 'Dados inválidos.'
        code = 'validation_error'
        details = normalized_details
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        message = str(getattr(exc, 'detail', 'Autenticação necessária.'))
        code = 'not_authenticated'
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        message = str(getattr(exc, 'detail', 'Você não tem permissão para executar esta ação.'))
        code = 'permission_denied'
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        message = str(getattr(exc, 'detail', 'Recurso não encontrado.'))
        code = 'not_found'
    elif isinstance(normalized_details, dict) and 'detail' in normalized_details and len(normalized_details) == 1:
        message = str(normalized_details['detail'])
        details = {}
    else:
        details = normalized_details

    response.data = build_error_payload(message=message, code=code, details=details)
    return response
