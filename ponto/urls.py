from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registrar/', views.registrar_ponto, name='registrar_ponto'),
    path('listar/', views.listar_pontos, name='listar_pontos'),
    path('historico-geral/pdf/', views.baixar_historico_geral_pdf, name='baixar_historico_geral_pdf'),
    path('historico-geral/Excel/', views.baixar_historico_geral_excel, name='baixar_historico_geral_excel'),
    path('admin/exportar-json/', views.exportar_json_admin, name='exportar_json_admin'),
    path('admin/importar-json/', views.importar_json_admin, name='importar_json_admin'),
    path('formulario/', views.formulario_view, name='formulario'),
    path('etiqueta/', views.gerar_etiqueta, name='gerar_etiqueta'),
    # path('baixar-excel/', views.baixar_presenca_excel, name='baixar_presenca_excel'),
]
