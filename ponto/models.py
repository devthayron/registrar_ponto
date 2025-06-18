from django.db import models

class RegistroPonto(models.Model):
    cpf = models.CharField(max_length=11)
    data = models.DateField()
    entrada = models.DateTimeField(null=True, blank=True)
    saida_almoco = models.DateTimeField(null=True, blank=True)
    volta_almoco = models.DateTimeField(null=True, blank=True)
    saida = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('cpf', 'data')
        verbose_name = "Registro de Ponto"
        verbose_name_plural = "Registros de Ponto"

    def __str__(self):
        return f"CPF {self.cpf} - Data {self.data}"
