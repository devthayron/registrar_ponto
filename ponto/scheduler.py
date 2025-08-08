from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from datetime import datetime
import os

def iniciar_agendador():
    scheduler = BackgroundScheduler()

    def fazer_backup():
        print(f"Backup automático iniciado às {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        call_command('exportar_backup')

    # Executa todos os dias às 13h10
    scheduler.add_job(fazer_backup, 'cron', hour=13, minute=10)

    scheduler.start()
