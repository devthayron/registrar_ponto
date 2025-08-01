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
from calendar import monthrange
from collections import defaultdict
from django.db.models.functions import TruncMonth

# ------------------  Usuário  ------------------
User = get_user_model()

# ------------------  Gerente  ------------------
def is_gerente(user):
    return user.nivel == 'gerente'

# ------------------  Filtro em exportações  ------------------

def filtrar_registros(request):
    cpf = request.GET.get('cpf', '').strip()
    cpf_limpo = cpf.replace('.', '').replace('-', '')
    lider_id = request.GET.get('lider', '').strip()
    data_inicial = request.GET.get('data_inicial')
    data_final = request.GET.get('data_final')

    registros = RegistroPonto.objects.select_related('colaborador').all()

    if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo.isdigit():
        registros = registros.filter(colaborador__cpf=cpf_limpo)

    if lider_id:
        registros = registros.filter(colaborador__lider_id=lider_id)

    if data_inicial:
        try:
            data_ini = date.fromisoformat(data_inicial)
            registros = registros.filter(data__gte=data_ini)
        except ValueError:
            pass

    if data_final:
        try:
            data_fim = date.fromisoformat(data_final)
            registros = registros.filter(data__lte=data_fim)
        except ValueError:
            pass

    return registros.order_by('colaborador__nome', 'data')


# ------------------  Excel  ------------------
@login_required
def baixar_historico_geral_excel(request):
    registros = filtrar_registros(request)

    wb = Workbook()
    ws = wb.active
    ws.title = "Histórico Geral"

    headers = ['CPF', 'Nome', 'Data', 'Entrada', 'Contrato',]  # 'Status'
    header_font = Font(bold=True)
    alignment = Alignment(horizontal='center')

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.alignment = alignment

    for row_num, registro in enumerate(registros, start=2):
        entrada_formatada = timezone.localtime(registro.entrada).strftime('%H:%M') if registro.entrada else '---'

        ws.cell(row=row_num, column=1, value=registro.colaborador.cpf)
        
        nome = registro.colaborador.nome
        if not registro.colaborador.is_active:
            nome = f"(INATIVO) {nome}"
        ws.cell(row=row_num, column=2, value=nome)
        ws.cell(row=row_num, column=3, value=registro.data.strftime('%d/%m/%Y') if registro.data else '')
        ws.cell(row=row_num, column=4, value=entrada_formatada)
        ws.cell(row=row_num, column=5, value=getattr(registro, 'lider_nome', ''))
        # ws.cell(row=row_num, column=6, value='ATIVO' if registro.colaborador.is_active else 'INATIVO')
        
    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        adjusted_width = max_length + 2
        ws.column_dimensions[col[0].column_letter].width = adjusted_width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename = "historico_geral.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'

    wb.save(response)
    return response

# ------------------  PDF  ------------------
@login_required
def baixar_historico_geral_pdf(request):
    registros = filtrar_registros(request).order_by('lider_nome', 'data', 'colaborador__nome')

    data_inicial = request.GET.get('data_inicial')
    data_final = request.GET.get('data_final')

    # Se não vieram, define como data de hoje
    hoje = localdate()
    if not data_inicial:
        data_inicial = hoje.strftime('%Y-%m-%d')
    if not data_final:
        data_final = hoje.strftime('%Y-%m-%d')

    html_string = render_to_string('ponto/pdf_pontos.html', {
        'registros': registros,
        'cpf': request.GET.get('cpf', ''),
        'lider': request.GET.get('lider', ''),
        'data_inicial': data_inicial,
        'data_final': data_final,
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
    data_hoje = localdate()
    data_inicial = request.GET.get('data_inicial') or data_hoje.isoformat()
    data_final = request.GET.get('data_final') or data_hoje.isoformat()


    filtros_usados = any([cpf_limpo, lider_id, data_inicial, data_final])
    registros = RegistroPonto.objects.select_related('colaborador').all()

    if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo.isdigit():
        registros = registros.filter(colaborador__cpf=cpf_limpo)

    if lider_id:
        registros = registros.filter(colaborador__lider_id=lider_id)

    if filtros_usados:
        try:
            if data_inicial:
                data_ini = date.fromisoformat(data_inicial)
                registros = registros.filter(data__gte=data_ini)
            if data_final:
                data_fim = date.fromisoformat(data_final)
                registros = registros.filter(data__lte=data_fim)
        except ValueError:
            messages.warning(request, 'Datas inválidas. Nenhum filtro de data foi aplicado.')
    else:
        data_hoje = localdate()
        registros = registros.filter(data=data_hoje)

    registros = registros.order_by('-data', 'lider_nome', '-entrada')
    paginator = Paginator(registros, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    lideres = Lider.objects.all()

    return render(request, 'ponto/listar_pontos.html', {
        'registros': page_obj.object_list,
        'cpf': cpf,
        'lider': lider_id,
        'page_obj': page_obj,
        'lideres': lideres,
        'data_inicial': data_inicial,
        'data_final': data_final,
        'request': request,
    })

@login_required
def tabela_presenca(request):
    cpf = request.GET.get('cpf', '').strip().replace('.', '').replace('-', '')
    setor = request.GET.get('setor', '')
    mes_str = request.GET.get('mes')  # exemplo: '2025-08'

    registros = RegistroPonto.objects.select_related('colaborador__lider')

    # Filtros simples
    if cpf and len(cpf) == 11 and cpf.isdigit():
        registros = registros.filter(colaborador__cpf=cpf)
    if setor:
        registros = registros.filter(colaborador__lider__nome=setor)

    # Lista de meses disponíveis
    meses_disponiveis = (
        registros
        .annotate(mes=TruncMonth('data'))
        .values_list('mes', flat=True)
        .distinct()
        .order_by('mes')
    )

    # Define mês atual
    if mes_str:
        try:
            mes_atual = datetime.strptime(mes_str + '-01', '%Y-%m-%d').date()
        except ValueError:
            mes_atual = meses_disponiveis.last() if meses_disponiveis else None
    else:
        mes_atual = meses_disponiveis.last() if meses_disponiveis else None

    if not mes_atual:
        contexto = {
            'tabela': {},
            'cpf': cpf,
            'setor': setor,
            'setores': [],
            'meses_disponiveis': [],
            'dias': [],
            'mes_atual': None,
            'total_por_dia': {},
        }
        return render(request, 'ponto/tabela_presenca.html', contexto)

    registros_mes = registros.filter(data__year=mes_atual.year, data__month=mes_atual.month)

    tabela = defaultdict(lambda: defaultdict(str))
    dias_com_presenca = set()

    for r in registros_mes:
        chave = (r.colaborador.nome, r.colaborador.cpf)
        tabela[chave][r.data.day] = 'S'
        dias_com_presenca.add(r.data.day)

    dias = sorted(list(dias_com_presenca))

    total_por_dia = {}
    for dia in dias:
        total_por_dia[dia] = sum(1 for presencas in tabela.values() if presencas.get(dia) == 'S')

    setores = (
        RegistroPonto.objects
        .select_related('colaborador__lider')
        .values_list('colaborador__lider__nome', flat=True)
        .distinct()
        .order_by('colaborador__lider__nome')
    )

    contexto = {
        'tabela': dict(tabela),
        'cpf': cpf,
        'setor': setor,
        'setores': setores,
        'meses_disponiveis': meses_disponiveis,
        'dias': dias,
        'mes_atual': mes_atual,
        'total_por_dia': total_por_dia,
    }
    return render(request, 'ponto/tabela_presenca.html', contexto)
