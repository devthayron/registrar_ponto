from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from ponto.models import Lider, Colaborador, RegistroPonto
import json
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Exporta os dados para backup automático em JSON'

    def handle(self, *args, **kwargs):
        dados = {
            'lideres': json.loads(serialize('json', Lider.objects.all())),
            'colaboradores': json.loads(serialize('json', Colaborador.objects.all())),
            'registros': json.loads(serialize('json', RegistroPonto.objects.all())),
        }

        data_hora = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        caminho_backup = f'backups/backup_{data_hora}.json'
        os.makedirs('backups', exist_ok=True)

        with open(caminho_backup, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Backup salvo em {caminho_backup}'))
