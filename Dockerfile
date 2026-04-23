FROM python:3.13-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV MARKITDOWN_ENABLE_PLUGINS=true

# Dependências de sistema para markitdown
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    exiftool \
    && rm -rf /var/lib/apt/lists/*

# Instalar o pacote MCP oficial + suporte a PDF
RUN pip install --no-cache-dir "markitdown-mcp" "markitdown[pdf]"

# O pacote expõe o CLI "markitdown-mcp"
ENTRYPOINT ["markitdown-mcp", "--http", "--host", "0.0.0.0", "--port", "10000"]
