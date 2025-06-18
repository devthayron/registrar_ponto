from django.contrib import admin
from .models import RegistroPonto, Colaborador, Lider


@admin.register(Lider)
class LiderAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('cpf_formatado', 'nome', 'lider')
    search_fields = ('cpf', 'nome')
    list_filter = ('lider',)

    def cpf_formatado(self, obj):
        cpf = obj.cpf
        # Formata CPF como 000.000.000-00
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    cpf_formatado.short_description = 'CPF'


@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = (
        'cpf_formatado',
        'data',
        'entrada',
        'saida_almoco',
        'volta_almoco',
        'saida',
        'lider_nome'
    )
    search_fields = (
        'colaborador__cpf',
        'colaborador__nome',
        'lider_nome'
    )
    list_filter = ('data', 'lider_nome')
    readonly_fields = ('lider_nome',)  # Evita edição manual para preservar histórico

    def cpf_formatado(self, obj):
        cpf = obj.colaborador.cpf
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    cpf_formatado.short_description = 'CPF'

    def save_model(self, request, obj, form, change):
        if not change:  # Se for registro novo
            if not obj.lider_nome and obj.colaborador.lider:
                obj.lider_nome = obj.colaborador.lider.nome
        # Se for edição, não altera lider_nome para preservar histórico
        super().save_model(request, obj, form, change)
