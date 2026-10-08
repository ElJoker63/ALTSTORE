FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y recursos estáticos
COPY . .

# Directorio de datos por defecto (puede montarse un volumen persistente)
ENV DATA_DIR=/app

EXPOSE 80

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]
