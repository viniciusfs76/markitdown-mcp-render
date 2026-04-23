FROM python:3.13-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV MARKITDOWN_ENABLE_PLUGINS=true

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    ffmpeg \
    exiftool \
    && rm -rf /var/lib/apt/lists/*

# Instalar markitdown com PDF + todas as extras e servidor MCP
RUN pip install --no-cache-dir \
    "markitdown[pdf,all]" \
    "mcp[server]" \
    fastapi \
    uvicorn \
    starlette

# Copiar o código customizado
COPY main.py .

# Executar o servidor MCP
CMD ["python", "main.py"]
