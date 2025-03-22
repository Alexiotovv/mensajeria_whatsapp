from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .serializers import UserSerializer, JustificacionesSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework import status

from .models import Justificaciones  # Importa tu modelo
from rest_framework.generics import ListAPIView

import os
import requests
import mimetypes
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime

from django.conf import settings
from dotenv import load_dotenv


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
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Número de Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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
                msg.body("Para matrículas y pagos, visita: https://cvallejoiquitos.com/pagos.")
            else:
                msg.body("Hola, selecciona una opción:\n1️⃣ Justificar asistencia\n2️⃣ Matrículas y pagos")
        
        elif estado == "esperando_dni":

            datos=obtener_datos_alumno(message)
            if datos:
                alumno = datos[0]
                nombre_completo = f"{alumno['ApellidoPaterno']} {alumno['ApellidoMaterno']}, {alumno['Nombres'].strip()}"
                grado = alumno["Grado"]
                seccion = alumno["Seccion"]
                
                estado_usuarios[sender]["dni"] = message
                estado_usuarios[sender]["nombre"] = nombre_completo
                estado_usuarios[sender]["grado"] = grado
                estado_usuarios[sender]["seccion"] = seccion
                msg.body(f"La justificación es para el alumno {nombre_completo} {grado}-{seccion}?\n1️⃣ Sí\n2️⃣ No")
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
                url_local = descargar_y_guardar_imagen(foto_url, request)
               

                dni = estado_usuarios[sender]["dni"]
                nombre = estado_usuarios[sender]["nombre"]
                grado = estado_usuarios[sender]["grado"]
                seccion = estado_usuarios[sender]["seccion"]
                descripcion = estado_usuarios[sender]["descripcion"]
                foto_url=url_local
                try:
                    guardar_justificacion(
                        dni=dni,
                        nombre=nombre,
                        grado=grado,
                        seccion=seccion,
                        descripcion=descripcion,    
                        foto_url=foto_url
                    )

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
    
def obtener_datos_alumno(dni):
    url = f"https://colcoopcv.com/buscar/alumno/{dni}"  # Construye la URL con el DNI
    try:
        response = requests.get(url)  # Hace la solicitud GET
        response.raise_for_status()  # Lanza un error si la solicitud falla
        return response.json()  # Devuelve la respuesta en formato JSON
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Manejo de errores
    
def guardar_justificacion(dni, nombre,grado,seccion, descripcion, foto_url=None):
    """
    Guarda una nueva justificación en la base de datos.

    :param dni: Documento de identidad del usuario
    :param nombre: Nombre del usuario
    :param descripcion: Descripción de la justificación
    :param foto_url: (Opcional) URL de la foto adjunta
    :return: Objeto Justificaciones creado
    """
    justificacion = Justificaciones.objects.create(
        dni=dni,
        nombre=nombre,
        grado=grado,
        seccion=seccion,
        descripcion=descripcion,
        foto_url=foto_url
    )
    return justificacion

# cuando se usa clase ya no va esto: @api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class ListarJustificaciones(ListAPIView):
    queryset = Justificaciones.objects.order_by('-hora_actual')  # Ordena de más reciente a más antigua
    serializer_class = JustificacionesSerializer

    def get_queryset(self):
        queryset = Justificaciones.objects.order_by('-hora_actual')
        
        año_actual = datetime.now().year
        queryset = queryset.filter(hora_actual__year=año_actual)  # Filtra por año actual

        grado = self.request.query_params.get('gradoFilter', None)
        seccion = self.request.query_params.get('seccionFilter', None)
        if grado:
            queryset = queryset.filter(grado=grado)
        if seccion:
            queryset = queryset.filter(seccion=seccion)
        return queryset

@api_view(['POST'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
def delete_justificacion(request, justificacion_id):
    try:
        justificacion = Justificaciones.objects.get(id=justificacion_id)  # Busca la justificación por ID
        justificacion.delete()  # Elimina el registro
        return Response({"mensaje": "Justificación eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)
    except Justificaciones.DoesNotExist:
        return Response({"error": "Justificación no encontrada"}, status=status.HTTP_404_NOT_FOUND)

def descargar_y_guardar_imagen(foto_url, request):
    """Descarga la imagen de Twilio y la guarda en 'media/justificaciones/' con URL completa."""

    # Obtener el dominio y protocolo automáticamente desde la petición
    dominio = request.build_absolute_uri('/')[:-1]  # Obtiene "http://localhost:8000" o "https://tudominio.com"

    # Nombre del archivo con timestamp
    nombre_archivo = datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"

    # Ruta donde se guardará la imagen
    carpeta_destino = os.path.join(settings.MEDIA_ROOT, "justificaciones")
    os.makedirs(carpeta_destino, exist_ok=True)  # Crea la carpeta si no existe

    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)

    try:
        # Descargar la imagen desde Twilio
        response = requests.get(foto_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), stream=True)
        response.raise_for_status()

        # Guardar la imagen localmente
        with open(ruta_completa, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        # Construir la URL completa con el dominio
        url_completa = f"{dominio}{settings.MEDIA_URL}justificaciones/{nombre_archivo}"
        return url_completa  # Guardar en la base de datos

    except requests.exceptions.RequestException as e:
        print(f"Error descargando la imagen: {e}")
        return None