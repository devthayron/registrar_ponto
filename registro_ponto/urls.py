from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login/')),  # redireciona para login na raiz
    path('', include('ponto.urls')),
]
