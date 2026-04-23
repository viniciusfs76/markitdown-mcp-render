from fastapi import FastAPI, HTTPException, Body
from markitdown import MarkItDown
from pydantic import BaseModel, HttpUrl
import os
import uvicorn

app = FastAPI(
    title="Triturador MarkItDown",
    description="Conversor de URLs e arquivos para Markdown. Use esta ação para ler conteúdo de sites e documentos.",
    version="1.0.0",
    servers=[{"url": "https://markitdown-mcp-lgqg.onrender.com", "description": "Servidor de Produção na Render"}]
)

md = MarkItDown()

class ConversionRequest(BaseModel):
    uri: HttpUrl

class ConversionResponse(BaseModel):
    markdown: str

@app.post("/convert", response_model=ConversionResponse)
async def convert_to_markdown(request: ConversionRequest):
    """
    Converte um recurso (URL) para Markdown.
    """
    try:
        result = md.convert_uri(str(request.uri))
        return ConversionResponse(markdown=result.markdown)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
