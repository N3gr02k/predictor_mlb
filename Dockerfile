# Dockerfile

# Usamos una imagen base oficial de Python
FROM python:3.11-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalamos todas las librerías
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el resto del código de nuestro proyecto al contenedor
COPY . .

# CAMBIO CLAVE: Damos permisos de ejecución a nuestro script
RUN chmod +x /app/src/run_daily_predictions.py

# El comando por defecto que se ejecutará cuando el contenedor inicie
# Esto será sobreescrito por el "Start Command" en Railway para el servicio web
CMD ["gunicorn", "src.app:app"]
