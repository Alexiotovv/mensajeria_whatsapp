from django.db import models
from django.utils.timezone import now

class Justificaciones(models.Model):
    dni = models.CharField(max_length=8)  # DNI como string de 8 caracteres
    nombre = models.CharField(max_length=255)  # Nombre completo
    descripcion = models.TextField(blank=True, null=True)  # Descripción opcional
    foto_url = models.URLField(max_length=500, blank=True, null=True)  # URL de la foto
    hora_actual = models.DateTimeField(default=now)  # Guarda la fecha y hora actual automáticamente

    def __str__(self):
        return f"{self.nombre} ({self.dni})"
