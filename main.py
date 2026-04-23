from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from markitdown import MarkItDown
from pydantic import BaseModel
from fastapi.openapi.utils import get_openapi
import os
import uvicorn
import tempfile
import base64

app = FastAPI()

# Configuração de CORS para permitir acesso do ChatGPT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

md = MarkItDown()

class ConversionRequest(BaseModel):
    uri: str = None
    file_base64: str = None
    filename: str = "document"

class ConversionResponse(BaseModel):
    markdown: str
    source: str  # "uri" ou "file"

@app.post("/convert", response_model=ConversionResponse, operation_id="convert_to_markdown")
async def convert_to_markdown(request: ConversionRequest):
    """
    Converte URI (URL) ou ficheiro local (base64) para Markdown.
    """
    try:
        if request.uri:
            result = md.convert_uri(request.uri)
            return ConversionResponse(markdown=result.markdown, source="uri")
        elif request.file_base64:
            # Decodificar base64 e salvar em ficheiro temporário
            file_content = base64.b64decode(request.file_base64)
            suffix = os.path.splitext(request.filename)[1] or ".bin"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name
            try:
                result = md.convert(tmp_path)
                return ConversionResponse(markdown=result.markdown, source="file")
            finally:
                os.unlink(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Forneça 'uri' ou 'file_base64'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload", response_model=ConversionResponse, operation_id="convert_file")
async def convert_file_upload(
    file: UploadFile = File(...),
):
    """
    Upload direto de ficheiro para conversão em Markdown.
    Suporta: PDF, DOCX, PPTX, XLSX, HTML, imagens, áudio, etc.
    """
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            result = md.convert(tmp_path)
            return ConversionResponse(markdown=result.markdown, source="file")
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Triturador - MarkItDown API",
        "version": "1.1.0",
        "endpoints": {
            "POST /convert": "Converte URI (url) ou ficheiro (base64) para Markdown",
            "POST /upload": "Upload direto de ficheiro para Markdown",
            "GET /health": "Health check"
        }
    }

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Triturador",
            "description": "Converte qualquer URL ou ficheiro para Markdown. Suporta PDF, DOCX, PPTX, XLSX, HTML, imagens, áudio.",
            "version": "1.1.0"
        },
        "servers": [{"url": "https://markitdown-mcp-lgqg.onrender.com"}],
        "paths": {
            "/convert": {
                "post": {
                    "operationId": "convert_url_or_file",
                    "summary": "Converter URL ou ficheiro base64 para Markdown",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "uri": {
                                            "type": "string",
                                            "description": "URL do site a converter"
                                        },
                                        "file_base64": {
                                            "type": "string",
                                            "description": "Conteúdo do ficheiro em base64"
                                        },
                                        "filename": {
                                            "type": "string",
                                            "description": "Nome original do ficheiro (ex: documento.pdf)"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Sucesso",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "markdown": {"type": "string"},
                                            "source": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/upload": {
                "post": {
                    "operationId": "convert_file_upload",
                    "summary": "Upload de ficheiro para Markdown",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "Ficheiro a converter"
                                        }
                                    },
                                    "required": ["file"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Sucesso",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "markdown": {"type": "string"},
                                            "source": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
