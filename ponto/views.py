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


@login_required
def baixar_presenca_excel(request):
    registros = filtrar_registros(request)

    if not request.GET.get('data_inicial') and not request.GET.get('data_final'):
        hoje = localdate()
        registros = registros.filter(data__month=hoje.month, data__year=hoje.year)

    presencas = defaultdict(lambda: {
        'nome': '',
        'cpf': '',
        'contrato': '',
        'dias': [''] * 31
    })

    for r in registros:
        dia = r.data.day
        cpf_colaborador = r.colaborador.cpf
        presencas[cpf_colaborador]['nome'] = r.colaborador.nome
        presencas[cpf_colaborador]['cpf'] = cpf_colaborador
        lider = r.colaborador.lider
        presencas[cpf_colaborador]['contrato'] = lider.nome if lider else '—'
        presencas[cpf_colaborador]['dias'][dia - 1] = 'S'

    # Criando a planilha sem o 'write_only=True' (modo normal)
    wb = Workbook()
    ws = wb.active
    ws.title = "Controle de Presença"

    # Escrevendo o cabeçalho
    headers = ["Funcionário", "CPF", "Contrato"] + [str(d) for d in range(1, 32)]
    ws.append(headers)

    # Formatando o cabeçalho
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Adicionando os dados de presença
    for dados in sorted(presencas.values(), key=lambda x: x['contrato']):
        linha = [dados['nome'], dados['cpf'], dados['contrato']] + dados['dias']
        ws.append(linha)

    # Calculando os totais por dia
    total_por_dia = ["Total", "", ""]
    for i in range(31):
        total = sum(1 for dados in presencas.values() if dados['dias'][i] == 'S')
        total_por_dia.append(total)
    ws.append(total_por_dia)

    # Ajustando a largura das colunas (com base no conteúdo)
    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    # Preparando a resposta para download
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="controle_presenca.xlsx"'
    wb.save(response)

    return response

# ------------------  PDF  ------------------
@login_required
def baixar_presenca_excel(request):
    registros = filtrar_registros(request)

    # Verifique se as datas estão corretamente configuradas, se não, filtra pelo mês atual
    if not request.GET.get('data_inicial') and not request.GET.get('data_final'):
        hoje = localdate()
        registros = registros.filter(data__month=hoje.month, data__year=hoje.year)

    # Criando um dicionário para armazenar as presenças dos colaboradores
    presencas = defaultdict(lambda: {
        'nome': '',
        'cpf': '',
        'contrato': '',
        'dias': [''] * 31  # Inicializa 31 dias
    })

    # Preenchendo as presenças de cada colaborador
    for r in registros:
        dia = r.data.day
        cpf_colaborador = r.colaborador.cpf
        presencas[cpf_colaborador]['nome'] = r.colaborador.nome
        presencas[cpf_colaborador]['cpf'] = cpf_colaborador
        lider = r.colaborador.lider
        presencas[cpf_colaborador]['contrato'] = lider.nome if lider else '—'
        presencas[cpf_colaborador]['dias'][dia - 1] = 'S'  # Marca a presença para o dia correto

    # Criando a planilha Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Controle de Presença"

    # Cabeçalho: Funcionário, CPF, Contrato + Dias de 1 a 31
    headers = ["Funcionário", "CPF", "Contrato"] + [str(d) for d in range(1, 32)]  # 31 colunas para os dias
    ws.append(headers)

    # Formatando o cabeçalho
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Adicionando as presenças de cada colaborador
    for dados in sorted(presencas.values(), key=lambda x: x['contrato']):
        linha = [dados['nome'], dados['cpf'], dados['contrato']] + dados['dias']  # Adiciona os 31 dias
        ws.append(linha)

    # Calculando os totais de presença por dia
    total_por_dia = ["Total", "", ""]  # A primeira célula vai mostrar "Total"
    for i in range(31):
        total = sum(1 for dados in presencas.values() if dados['dias'][i] == 'S')  # Conta as presenças por dia
        total_por_dia.append(total)  # Adiciona o total para o dia
    ws.append(total_por_dia)

    # Ajustando a largura das colunas
    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    # Preparando a resposta para download do arquivo
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="controle_presenca.xlsx"'
    wb.save(response)

    return response



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
