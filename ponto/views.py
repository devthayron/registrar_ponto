from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import RegistroPonto, Colaborador
from django.contrib.auth.models import User


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Usuário e senha fixos (para ambiente de testes)
        if username == 'admin' and password == 'admin123':
            user, _ = User.objects.get_or_create(username='admin')
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
        cpf_limpo = cpf.replace('.', '').replace('-', '')

        if not (cpf_limpo.isdigit() and len(cpf_limpo) == 11):
            messages.error(request, 'CPF inválido. Informe exatamente 11 dígitos numéricos.')
            return redirect('registrar_ponto')

        colaborador = Colaborador.objects.filter(cpf=cpf_limpo).first()
        if not colaborador:
            messages.error(request, 'CPF não cadastrado no sistema. Contate o administrador.')
            return redirect('registrar_ponto')

        hoje = timezone.localdate()
        agora = timezone.now()

        try:
            registro, created = RegistroPonto.objects.get_or_create(
                colaborador=colaborador,
                data=hoje
            )

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

            if created:
                registro.lider_nome = colaborador.lider.nome if colaborador.lider else ''

            registro.save()
            messages.success(request, 'Ponto registrado com sucesso!')

        except Exception as e:
            messages.error(request, f'Erro ao registrar ponto: {e}')

        return redirect('registrar_ponto')

    return render(request, 'ponto/registrar_ponto.html')


@login_required
def listar_pontos(request):
    cpf = request.GET.get('cpf', '').strip()
    cpf_limpo = cpf.replace('.', '').replace('-', '')

    registros = RegistroPonto.objects.select_related('colaborador').all()

    if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo.isdigit():
        registros = registros.filter(colaborador__cpf=cpf_limpo)

    registros = registros.order_by('-data', '-entrada')

    paginator = Paginator(registros, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ponto/listar_pontos.html', {
        'registros': page_obj.object_list,
        'cpf': cpf,
        'page_obj': page_obj,
    })
