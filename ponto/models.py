from django.db import models
from django.contrib.auth.models import AbstractUser

class UsuarioPersonalizado(AbstractUser):
    NIVEIS = (
        ('usuario', 'Usuário'),
        ('gerente', 'Gerente'),
    )
    nivel = models.CharField(max_length=10, choices=NIVEIS, default='usuario')

    def __str__(self):
        return self.username  


class Lider(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Colaborador(models.Model):
    cpf = models.CharField(max_length=11, unique=True)
    nome = models.CharField(max_length=100, blank=True)
    lider = models.ForeignKey(
        Lider,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='colaboradores'
    )

    def __str__(self):
        return f'{self.nome} ({self.cpf})' if self.nome else self.cpf


class RegistroPonto(models.Model):
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.CASCADE,
        related_name='registros'
    )
    data = models.DateField()
    entrada = models.DateTimeField(null=True, blank=True)
    saida = models.DateTimeField(null=True, blank=True)

    lider_nome = models.CharField(
        max_length=100,
        blank=True,
        help_text='Nome do líder no momento do registro (congelado para histórico)'
    )

    class Meta:
        unique_together = ('colaborador', 'data')
        verbose_name = "Registro de Ponto"
        verbose_name_plural = "Registros de Ponto"

    def save(self, *args, **kwargs):
        if not self.lider_nome and self.colaborador.lider:
            self.lider_nome = self.colaborador.lider.nome
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.colaborador.cpf} - {self.data}"
