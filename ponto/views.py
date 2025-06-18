from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import RegistroPonto
from django.contrib.auth.models import User


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Usuário e senha fixos (para ambiente de testes)
        if username == 'admin' and password == 'admin123':
            user, created = User.objects.get_or_create(username='admin')
            login(request, user)
            return redirect('registrar_ponto')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')

    return render(request, 'ponto/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def registrar_ponto(request):
    if request.method == 'POST':
        cpf = request.POST.get('cpf', '').strip()

        # Validação básica de CPF
        if not (cpf.isdigit() and len(cpf) == 11):
            messages.error(request, 'CPF inválido. Informe exatamente 11 dígitos numéricos.')
            return redirect('registrar_ponto')

        hoje = timezone.localdate()
        agora = timezone.now()

        registro, created = RegistroPonto.objects.get_or_create(cpf=cpf, data=hoje)

        if not registro.entrada:
            registro.entrada = agora
        elif not registro.saida_almoco:
            registro.saida_almoco = agora
        elif not registro.volta_almoco:
            registro.volta_almoco = agora
        elif not registro.saida:
            registro.saida = agora
        else:
            messages.error(request, 'Todos os horários já foram registrados para hoje.')
            return redirect('registrar_ponto')

        registro.save()
        messages.success(request, 'Ponto registrado com sucesso!')
        return redirect('registrar_ponto')

    return render(request, 'ponto/registrar_ponto.html')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import RegistroPonto
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator


from django.db.models import Value
from django.db.models.functions import Lower
from django.db.models import CharField

@login_required
def listar_pontos(request):
    cpf = request.GET.get('cpf', '').strip()

    # Query base
    registros = RegistroPonto.objects.all()

    # CPFs únicos para filtro (ordenados)
    cpfs_unicos = registros.order_by('cpf').values_list('cpf', flat=True).distinct()

    # Filtrar se cpf foi passado e válido
    if cpf and len(cpf) == 11 and cpf.isdigit():
        registros = registros.filter(cpf=cpf)

    registros = registros.order_by('-data')

    paginator = Paginator(registros, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ponto/listar_pontos.html', {
        'registros': page_obj.object_list,
        'cpf': cpf,
        'cpfs_unicos': cpfs_unicos,
        'page_obj': page_obj,
    })


