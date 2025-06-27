from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado, RegistroPonto, Colaborador, Lider
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.http import HttpResponse
from .utils_etiqueta import gerar_etiqueta
from django.shortcuts import render
from django.utils.html import format_html
from django.shortcuts import redirect

@admin.register(UsuarioPersonalizado)
class UsuarioPersonalizadoAdmin(UserAdmin):
    model = UsuarioPersonalizado

    # Campos que aparecem na listagem
    list_display = ('username', 'email', 'first_name', 'last_name', 'nivel', 'is_staff', 'is_active')
    list_filter = ('nivel', 'is_staff', 'is_active')

    # Campos para busca
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Campos exibidos no formulário de edição/criação
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informações Pessoais'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissões'), {'fields': ('nivel', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Datas importantes'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'nivel', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    ordering = ('username',)


@admin.register(Lider)
class LiderAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('cpf_formatado', 'nome', 'lider', 'botao_etiqueta')
    search_fields = ('cpf', 'nome')
    list_filter = ('lider',)

    def cpf_formatado(self, obj):
        cpf = obj.cpf
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    cpf_formatado.short_description = 'CPF'

    def botao_etiqueta(self, obj):
        return format_html(
            '<a class="button" href="/etiqueta/{}/" target="_blank">Gerar Etiqueta</a>',
            obj.id
        )
    botao_etiqueta.short_description = 'Etiqueta'
    botao_etiqueta.allow_tags = True

    def gerar_etiqueta_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Selecione apenas um colaborador para gerar a etiqueta.", level='error')
            return

        colaborador = queryset.first()
        etiqueta_url = self.get_etiqueta_url(colaborador)
        voltar_para = request.get_full_path()

        return render(request, 'ponto/abrir_etiqueta.html', {
            'etiqueta_url': etiqueta_url,
            'voltar_para': voltar_para,
        })

    def etiqueta_view(self, request, colaborador_id):
        from .models import Colaborador

        colaborador = Colaborador.objects.get(id=colaborador_id)
        nome_colaborador = colaborador.nome
        nome_lider = colaborador.lider.nome if colaborador.lider else 'Sem líder'
        dados_qr = colaborador.cpf  # pode ser alterado para outro identificador

        imagem_buffer = gerar_etiqueta(nome_colaborador, nome_lider, dados_qr)

        return HttpResponse(imagem_buffer.getvalue(), content_type='image/png')

@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = (
        'nome_colaborador',
        'cpf_formatado',
        'data',
        'entrada',
        'saida',
        'lider_nome'
    )
    search_fields = (
        'colaborador__cpf',
        'colaborador__nome',
        'lider_nome'
    )
    list_filter = ('data', 'lider_nome')  
    readonly_fields = ('lider_nome',)  # Evita edição para preservar histórico

    def cpf_formatado(self, obj):
        cpf = obj.colaborador.cpf
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    cpf_formatado.short_description = 'CPF'

    def nome_colaborador(self, obj):
        return obj.colaborador.nome
    nome_colaborador.admin_order_field = 'colaborador__nome'  
    nome_colaborador.short_description = 'Nome'

    def save_model(self, request, obj, form, change):
        if not change:  # Se for um novo registro
            if not obj.lider_nome and obj.colaborador.lider:
                obj.lider_nome = obj.colaborador.lider.nome
        
        if change:
            registros_futuros = RegistroPonto.objects.filter(
                colaborador=obj.colaborador,
                data__gte=obj.data
            )
            for reg in registros_futuros:
                reg.lider_nome = obj.colaborador.lider.nome
                reg.save()

        super().save_model(request, obj, form, change)
