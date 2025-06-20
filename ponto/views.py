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
    headers = ['CPF', 'Nome', 'Data', 'Entrada', 'Saída', 'Líder (no registro)']
    header_font = Font(bold=True)
    alignment = Alignment(horizontal='center')

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.alignment = alignment

    # Preenche as linhas
    for row_num, registro in enumerate(registros, start=2):
        ws.cell(row=row_num, column=1, value=registro.colaborador.cpf)
        ws.cell(row=row_num, column=2, value=registro.colaborador.nome)
        ws.cell(row=row_num, column=3, value=registro.data.strftime('%d/%m/%Y') if registro.data else '')
        ws.cell(row=row_num, column=4, value=registro.entrada.strftime('%H:%M') if registro.entrada else '---')
        ws.cell(row=row_num, column=5, value=registro.saida.strftime('%H:%M') if registro.saida else '---')
        ws.cell(row=row_num, column=6, value=registro.lider_nome if hasattr(registro, 'lider_nome') else '')

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
    registros = RegistroPonto.objects.select_related('colaborador').order_by('colaborador__nome', 'data')

    html_string = render_to_string('ponto/pdf_pontos.html', {
        'registros': registros,
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


# ------------------  Registro  ------------------
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
            elif not registro.saida:
                registro.saida = agora
            else:
                messages.error(request, 'Entrada e saída já registradas para hoje.')
                return redirect('registrar_ponto')

            registro.save()
            messages.success(request, 'Ponto registrado com sucesso!')

        except Exception as e:
            messages.error(request, f'Erro ao registrar ponto: {e}')

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

    registros = RegistroPonto.objects.select_related('colaborador').all()

    if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo.isdigit():
        registros = registros.filter(colaborador__cpf=cpf_limpo)

    if lider_id:
        registros = registros.filter(colaborador__lider_id=lider_id)

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
    })


