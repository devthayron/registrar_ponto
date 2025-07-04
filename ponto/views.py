from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import RegistroPonto, Colaborador, Lider
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
from datetime import datetime
from openpyxl.styles import Font, Alignment
from openpyxl import Workbook
from datetime import timedelta,date
from django.utils.timezone import localdate
# ------------------  Usuário  ------------------
User = get_user_model()

# ------------------  Gerente  ------------------
def is_gerente(user):
    return user.nivel == 'gerente'

# ------------------  Excel  ------------------

@login_required
def baixar_historico_geral_excel(request):
    # Query com registros ordenados como no PDF
    registros = RegistroPonto.objects.select_related('colaborador').order_by('colaborador__nome', 'data')

    # Cria workbook e planilha
    wb = Workbook()
    ws = wb.active
    ws.title = "Histórico Geral"

    # Cabeçalhos
    headers = ['CPF', 'Nome', 'Data', 'Entrada', 'Saída', 'Conferente']
    header_font = Font(bold=True)
    alignment = Alignment(horizontal='center')

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.alignment = alignment

    # Preenche as linhas
    for row_num, registro in enumerate(registros, start=2):
        entrada_formatada = timezone.localtime(registro.entrada).strftime('%H:%M') if registro.entrada else '---'
        saida_formatada = timezone.localtime(registro.saida).strftime('%H:%M') if registro.saida else '---'

        ws.cell(row=row_num, column=1, value=registro.colaborador.cpf)
        ws.cell(row=row_num, column=2, value=registro.colaborador.nome)
        ws.cell(row=row_num, column=3, value=registro.data.strftime('%d/%m/%Y') if registro.data else '')
        ws.cell(row=row_num, column=4, value=entrada_formatada)
        ws.cell(row=row_num, column=5, value=saida_formatada)
        ws.cell(row=row_num, column=6, value=getattr(registro, 'lider_nome', ''))

    # Ajusta largura das colunas para melhorar visualização
    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        adjusted_width = max_length + 2
        ws.column_dimensions[col[0].column_letter].width = adjusted_width

    # Prepara resposta para download do Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename = f"historico_geral.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'

    wb.save(response)
    return response


# ------------------  PDF  ------------------
@login_required
def baixar_historico_geral_pdf(request):
    cpf = request.GET.get('cpf', '').strip()
    cpf_limpo = cpf.replace('.', '').replace('-', '')
    lider_id = request.GET.get('lider', '').strip()
    data = request.GET.get('data')

    registros = RegistroPonto.objects.select_related('colaborador').all()

    # Filtra por CPF, se válido
    if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo.isdigit():
        registros = registros.filter(colaborador__cpf=cpf_limpo)

    # Filtra por líder, se informado
    if lider_id:
        registros = registros.filter(colaborador__lider_id=lider_id)

    # Filtra por data, padrão para hoje se não informado
    if not data:
        data = localdate()
    else:
        try:
            data = date.fromisoformat(data)
        except ValueError:
            data = localdate()

    registros = registros.filter(data=data).order_by('colaborador__nome', 'data')

    html_string = render_to_string('ponto/pdf_pontos.html', {
        'registros': registros,
        'cpf': cpf,
        'lider': lider_id,
        'data': data.strftime('%Y-%m-%d'),
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=historico_geral_ponto.pdf'

    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)

    return response

# ------------------  Login  ------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.nivel == 'gerente':
                return redirect('listar_pontos')  
            else:
                return redirect('registrar_ponto')  
        else:
            messages.error(request, 'Usuário ou senha incorretos.')

    return render(request, 'ponto/login.html')

# ------------------  logout  ------------------
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ------------------ Registro ------------------
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

            # Se a entrada já foi registrada, não registra novamente
            if registro.entrada:
                messages.error(request, 'Entrada já registrada para hoje.')
                return redirect('registrar_ponto')

            # Bloqueio por tempo para evitar múltiplos registros rápidos
            intervalo = timedelta(seconds=10)
            if registro.entrada and (agora - registro.entrada) < intervalo:
                messages.error(request, 'Leitura ignorada: entrada já registrada recentemente.')
                return redirect('registrar_ponto')

            # Registrar apenas a entrada
            registro.entrada = agora
            registro.save()
            messages.success(request, 'Entrada registrada com sucesso!')

        except Exception as e:
            messages.error(request, f'Erro ao registrar entrada: {e}')

        return redirect('registrar_ponto')

    return render(request, 'ponto/registrar_ponto.html')



# ------------------  Listagem  ------------------
@login_required
def listar_pontos(request):
    if not is_gerente(request.user):
        messages.error(request, 'Acesso restrito. Apenas gerentes podem acessar esta página.')
        return redirect('registrar_ponto')

    cpf = request.GET.get('cpf', '').strip()
    cpf_limpo = cpf.replace('.', '').replace('-', '')
    lider_id = request.GET.get('lider', '').strip()
    data = request.GET.get('data')

    # Checar se algum filtro foi usado
    filtros_usados = any([cpf_limpo, lider_id, data])

    registros = RegistroPonto.objects.select_related('colaborador').all()

    if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo.isdigit():
        registros = registros.filter(colaborador__cpf=cpf_limpo)

    if lider_id:
        registros = registros.filter(colaborador__lider_id=lider_id)

    # Se algum filtro foi usado, aplicar o filtro de data
    if filtros_usados:
        if data:
            try:
                data_formatada = date.fromisoformat(data)
                registros = registros.filter(data=data_formatada)
            except ValueError:
                messages.warning(request, 'Data inválida. Nenhum filtro de data foi aplicado.')
        # Se data foi enviada mas inválida, não aplica nada
    else:
        # Nenhum filtro → padrão: mostrar registros de hoje
        data = localdate()
        registros = registros.filter(data=data)

    registros = registros.order_by('-data', '-entrada')

    paginator = Paginator(registros, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    lideres = Lider.objects.all()

    return render(request, 'ponto/listar_pontos.html', {
        'registros': page_obj.object_list,
        'cpf': cpf,
        'lider': lider_id,
        'page_obj': page_obj,
        'lideres': lideres,
        'data': data if isinstance(data, str) else data.strftime('%Y-%m-%d'),
    })


