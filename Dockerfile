# Usar una imagen base de Python 3.10.12
FROM python:3.10.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pkg-config \
    libmariadb-dev \  # Usar libmariadb-dev en lugar de libmysqlclient-dev
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto 8000 (puerto por defecto de Django)
EXPOSE 8000
# Comando para ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "tu_app_django.wsgi:application"]