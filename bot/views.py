from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .serializers import UserSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework import status



import os
import requests
import mimetypes
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime




@api_view(['POST'])
def login(request):
    user = get_object_or_404(User,username=request.data['username'])

    if not user.check_password(request.data['password']):
      return Response({'error':"Invalid password"}, status = status.HTTP_400_BAD_REQUEST)
    
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(instance=user)
    return Response({'token':token.key,'user':serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()  # Guarda el usuario y obtén la instancia
        
        # Cifra la contraseña usando set_password
        user.set_password(serializer.validated_data['password'])
        user.save()  # Guarda el usuario con la contraseña cifrada

        # Crea un token para el usuario
        token = Token.objects.create(user=user)

        return Response(
            {'token': token.key, 'user': serializer.data},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(instance=request.user)
    return Response(serializer.data,status=status.HTTP_200_OK)
    #return Response('You are login with {}'.format(request.user.username),status=status.HTTP_200_OK)

# Configuración de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Número de Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Base de datos simulada (JSON en el código)
estudiantes = {
    "12345678": "JUAN PEREZ",
    "87654321": "MARIA LOPEZ",
}

# Diccionario para almacenar el estado de la conversación
estado_usuarios = {}

@csrf_exempt  # Desactiva la protección CSRF para esta vista
def whatsapp(request):
    if request.method == "POST":
        sender = request.POST.get("From")  # Número del usuario
        message = request.POST.get("Body", "").strip()  # Mensaje recibido

        response = MessagingResponse()
        msg = response.message()

        if sender not in estado_usuarios:
            estado_usuarios[sender] = {"estado": "menu"}
        
        estado = estado_usuarios[sender]["estado"]

        if estado == "menu":
            if message == "1":
                msg.body("Por favor, ingresa el DNI del estudiante:")
                estado_usuarios[sender]["estado"] = "esperando_dni"
            elif message == "2":
                msg.body("Para matrículas y pagos, visita: https://miportal.com/pagos o responde con tu consulta específica.")
            else:
                msg.body("Hola, selecciona una opción:\n1️⃣ Justificar asistencia\n2️⃣ Matrículas y pagos")
        
        elif estado == "esperando_dni":
            if message in estudiantes:
                estado_usuarios[sender]["dni"] = message
                estado_usuarios[sender]["nombre"] = estudiantes[message]
                msg.body(f"La justificación es para el alumno {estudiantes[message]}?\n1️⃣ Sí\n2️⃣ No")
                estado_usuarios[sender]["estado"] = "confirmar_estudiante"
            else:
                msg.body("DNI no encontrado. Por favor, ingresa un DNI válido:")
        
        elif estado == "confirmar_estudiante":
            if message == "1":
                msg.body("Por favor, ingresa la descripción del motivo de la inasistencia:")
                estado_usuarios[sender]["estado"] = "esperando_descripcion"
            elif message == "2":
                msg.body("Operación cancelada. Volviendo al menú principal...\n1️⃣ Justificar asistencia\n2️⃣ Matrículas y pagos")
                estado_usuarios[sender]["estado"] = "menu"
            else:
                msg.body("Por favor, selecciona una opción válida:\n1️⃣ Sí\n2️⃣ No")
        
        elif estado == "esperando_descripcion":
            estado_usuarios[sender]["descripcion"] = message
            msg.body("⚠️ Por favor, envía una foto de la atención médica.")
            estado_usuarios[sender]["estado"] = "esperando_foto"
        
        elif estado == "esperando_foto":
            if "MediaUrl0" in request.POST:
                foto_url = request.POST["MediaUrl0"]
                dni = estado_usuarios[sender]["dni"]
                nombre = estado_usuarios[sender]["nombre"]
                descripcion = estado_usuarios[sender]["descripcion"]

                try:
                    hora_actual = datetime.now().strftime("%H:%M:%S")

                    # Guardar información en un archivo .txt
                    with open("justificaciones.txt", "a") as file:
                        file.write(f"DNI: {dni}\n")
                        file.write(f"Nombre: {nombre}\n")
                        file.write(f"Descripción: {descripcion}\n")
                        file.write(f"Foto: {foto_url}\n")
                        file.write(f"Hora: {hora_actual}\n")
                        file.write("-" * 50 + "\n")

                    msg.body("✅ Justificación registrada exitosamente. La foto ha sido guardada.")
                except Exception as e:
                    msg.body(f"❌ Error guardando la justificación: {str(e)}")

            else:
                msg.body("❌ No se recibió ninguna imagen. Por favor, intenta nuevamente.")

            # Resetear estado a menú después de procesar la justificación
            estado_usuarios[sender]["estado"] = "menu"

        return HttpResponse(str(response), content_type="application/xml")  # Responde con XML
    else:
        return HttpResponse("Método no permitido", status=405)