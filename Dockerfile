FROM python:3.12-slim

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar as bibliotecas necessárias
RUN pip install --no-cache-dir markitdown fastapi uvicorn pydantic

# Copiar o código customizado (main.py)
COPY main.py .

# Expor a porta
EXPOSE 10000

# Executar a API via FastAPI/Uvicorn
CMD ["python", "main.py"]
