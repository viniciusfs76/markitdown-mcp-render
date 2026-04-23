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
    openapi_schema = get_openapi(
        title="Triturador",
        version="1.0.0",
        description="Conversor de sites para Markdown. IMPORTANTE: Use o endpoint /convert passando um JSON com o campo 'uri'.",
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.0"
    openapi_schema["servers"] = [{"url": "https://markitdown-mcp-lgqg.onrender.com"}]
    # Garantir que a operação tenha um ID amigável
    if "/convert" in openapi_schema["paths"]:
        openapi_schema["paths"]["/convert"]["post"]["operationId"] = "convert_url"
        
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
