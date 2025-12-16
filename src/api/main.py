from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.council import run_council_async
import os

app = FastAPI()

# Serve UI static files - path relative to project root
ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui")
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
async def serve_ui():
    """Serve the main UI page"""
    index_path = os.path.join(ui_dir, "index.html")
    return FileResponse(index_path)

@app.post("/council")
async def council_endpoint(request: PromptRequest):
    try:
        result = await run_council_async(request.prompt)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

