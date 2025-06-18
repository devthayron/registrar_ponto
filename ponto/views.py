from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import RegistroPonto
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Usuário fixo e senha fixa
        if username == 'admin' and password == 'admin123':
            from django.contrib.auth.models import User
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
        cpf = request.POST.get('cpf')
        if not cpf or len(cpf) != 11 or not cpf.isdigit():
            messages.error(request, 'CPF inválido. Informe os 11 dígitos numéricos.')
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
            messages.info(request, 'Todos os horários já foram registrados para hoje.')
            return redirect('registrar_ponto')

        registro.save()
        messages.success(request, 'Ponto registrado com sucesso!')

        return redirect('registrar_ponto')

    return render(request, 'ponto/registrar_ponto.html')


@login_required
def listar_pontos(request):
    cpf = request.GET.get('cpf')
    if cpf and len(cpf) == 11 and cpf.isdigit():
        registros = RegistroPonto.objects.filter(cpf=cpf).order_by('-data')
    else:
        registros = RegistroPonto.objects.all().order_by('-data')
        cpf = None  # Evita exibir o título "Registros para CPF" se não foi pesquisado
    return render(request, 'ponto/listar_pontos.html', {'registros': registros, 'cpf': cpf})
