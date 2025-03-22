from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Justificaciones

class UserSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True)  # Campo de solo escritura
  class Meta:
    model=User
    fields=['id','username','email', 'password']
    
class JustificacionesSerializer(serializers.ModelSerializer):
  class Meta:
    model=Justificaciones
    fields=['id','dni','nombre','grado','seccion','descripcion','foto_url','hora_actual']
  