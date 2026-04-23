FROM python:3.12-slim

WORKDIR /app

# Instalar dependências de sistema necessárias para o MarkItDown (ex: para PDFs/Imagens)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar a versão oficial do markitdown-mcp e uvicorn
RUN pip install --no-cache-dir markitdown-mcp uvicorn

# Expor a porta que o Render usará
EXPOSE 10000

# O Render injeta a variável de ambiente $PORT automaticamente. 
# Iniciar via Uvicorn diretamente, ou usando o entrypoint nativo
CMD markitdown-mcp --http --host 0.0.0.0 --port ${PORT:-10000}
