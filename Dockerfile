# Usar una imagen base de Python 3.10.12 slim (versión ligera)
FROM python:3.10.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto 8000 (puerto por defecto de Gunicorn)
EXPOSE 8000

# Comando para ejecutar Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mensajeriaval.wsgi:application"]

# # Usar una imagen base de Python 3.10.12 slim (versión ligera)
# FROM python:3.10.12

# # Establecer el directorio de trabajo
# WORKDIR /app

# # Instalar dependencias del sistema necesarias para mysqlclient
# RUN apt-get update && apt-get install -y \
#     gcc \
#     python3-dev \
#     default-libmysqlclient-dev \
#     pkg-config \
#     apache2 \
#     apache2-dev \
#     libapache2-mod-wsgi-py3 && \
#     a2enmod wsgi && \
#     rm -rf /var/lib/apt/lists/*

# # Copiar el archivo de dependencias
# COPY requirements.txt .

# # Instalar las dependencias de Python
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt

# # Configuramos Apache para servir Django
# COPY apache/apache-config.conf /etc/apache2/sites-available/000-default.conf

# # Habilitamos módulos necesarios en Apache
# RUN a2enmod wsgi

# # Copiar el resto del código de la aplicación
# COPY . .

# # Exponemos el puerto 80 para recibir tráfico HTTP
# EXPOSE 8000

# # Comando para iniciar Apache
# CMD ["apachectl", "-D", "FOREGROUND"]