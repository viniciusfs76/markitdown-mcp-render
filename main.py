from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from markitdown import MarkItDown
from pydantic import BaseModel
from fastapi.openapi.utils import get_openapi
import os
import uvicorn

app = FastAPI()

# Configuração de CORS para permitir acesso do ChatGPT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com", "https://openai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

md = MarkItDown()

class ConversionRequest(BaseModel):
    uri: str

class ConversionResponse(BaseModel):
    markdown: str

@app.post("/convert", response_model=ConversionResponse, operation_id="convert_to_markdown")
async def convert_to_markdown(request: ConversionRequest):
    """
    Converte uma URL para Markdown.
    """
    try:
        result = md.convert_uri(request.uri)
        return ConversionResponse(markdown=result.markdown)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Schema plano para máxima compatibilidade com ChatGPT
    openapi_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Triturador",
            "description": "Converte qualquer site para Markdown. Basta passar a URL.",
            "version": "1.0.0"
        },
        "servers": [{"url": "https://markitdown-mcp-lgqg.onrender.com"}],
        "paths": {
            "/convert": {
                "post": {
                    "operationId": "convert_url",
                    "summary": "Converter URL para Markdown",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "uri": {
                                            "type": "string",
                                            "description": "A URL do site a ser convertido"
                                        }
                                    },
                                    "required": ["uri"]
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
                                            "markdown": {"type": "string"}
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
