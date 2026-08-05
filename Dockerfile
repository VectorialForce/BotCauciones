FROM python:3.12-slim

WORKDIR /app

# Dependencias de sistema: psycopg2, Chromium, Xvfb
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    xvfb \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Healthcheck - verifica conexión a PostgreSQL usando variables de entorno del container
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.database import verificar_conexion; verificar_conexion()" || exit 1

# Xvfb crea un display virtual para que Chromium corra con GUI
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && python main.py"]
