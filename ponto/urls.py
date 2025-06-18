from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registrar/', views.registrar_ponto, name='registrar_ponto'),
    path('listar/', views.listar_pontos, name='listar_pontos'),
]
