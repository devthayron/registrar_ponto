from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado, RegistroPonto, Colaborador, Lider
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin import site as admin_site


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
    list_display = ('cpf_formatado', 'nome', 'lider')
    search_fields = ('cpf', 'nome')
    list_filter = ('lider','is_active')  
    
    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     return qs.filter(is_active=True)  # filtra só ativos

    def cpf_formatado(self, obj):
        cpf = obj.cpf
        # Formata CPF como 000.000.000-00
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    cpf_formatado.short_description = 'CPF'


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

# Hook para adicionar os botões no dashboard padrão
# Guarda o método index original
original_admin_index = AdminSite.index

def custom_admin_index(self, request, extra_context=None):
    if extra_context is None:
        extra_context = {}

    if request.user.is_staff:
        extra_context['extra_buttons'] = format_html("""
            <div style="margin: 20px 0;">
                <a class="button" href="{}">📤 Exportar Dados JSON</a>
                <a class="button" href="{}">📥 Importar Dados JSON</a>
            </div>
        """, reverse("exportar_json_admin"), reverse("importar_json_admin"))

    # Chama o método original corretamente com os 3 argumentos
    return original_admin_index(self, request, extra_context=extra_context)

admin.site.index = custom_admin_index.__get__(admin.site, AdminSite)

