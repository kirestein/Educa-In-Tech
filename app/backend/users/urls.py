from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import assign_role, healthcheck, me

urlpatterns = [
    path('health/', healthcheck, name='users-healthcheck'),
    path('token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', me, name='users-me'),
    path('roles/assign/', assign_role, name='users-assign-role'),
]