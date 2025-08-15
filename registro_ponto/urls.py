from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from ponto import views 

urlpatterns = [
    path('admin/exportar-json/', views.exportar_json_admin, name='exportar_json_admin'),
    path('admin/importar-json/', views.importar_json_admin, name='importar_json_admin'),
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login/')),  # redireciona para login na raiz
    path('', include('ponto.urls')),
    path('', include('ponto.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
