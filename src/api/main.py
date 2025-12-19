from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from src.council import run_council_sync, run_curator_only
import os
import json
import asyncio

app = FastAPI()

# Persistent conversation history
MEMORY_FILE = "memory.json"

def load_memory():
    """Load conversation history from memory.json"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(history):
    """Save conversation history to memory.json"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save memory: {e}")

# Serve UI static files - path relative to project root
ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui")
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

class PromptRequest(BaseModel):
    prompt: str


async def council_stream(prompt: str):
    """Stream council deliberation via SSE"""
    import asyncio
    loop = asyncio.get_event_loop()
    
    try:
        # Run Curator first (fast)
        curator_result = await loop.run_in_executor(None, run_curator_only, prompt, None)
        
        if "error" in curator_result:
            yield f"data: {json.dumps({'type': 'error', 'content': curator_result['error']})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            return
        
        # Yield Curator response
        yield f"data: {json.dumps({'type': 'agent', 'agent': 'Curator'})}\n\n"
        curator_output = curator_result.get('output', '')
        # Yield full curator output at once (it's already fast)
        yield f"data: {json.dumps({'type': 'content', 'content': curator_output})}\n\n"
        
        # Check if self-improvement mode (bypass curator refinement)
        is_self_improve = "self-improvement mode" in prompt.lower() or "self-improve" in prompt.lower()
        
        # If asking for confirmation and not self-improve mode, stop here
        if curator_result.get('asking_confirmation') and not is_self_improve:
            # Send any remaining content first
            yield f"data: {json.dumps({'type': 'content', 'content': '\\n\\nReady for full council deliberation? (Full deliberation will take ~12 minutes)'})}\n\n"
            yield f"data: {json.dumps({'done': True, 'needs_confirmation': True})}\n\n"
            return
        
        # Run full council
        result = await loop.run_in_executor(None, run_council_sync, prompt, None, is_self_improve)
        
        if "error" in result:
            yield f"data: {json.dumps({'type': 'error', 'content': result['error']})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            return
        
        # Stream each agent's output
        agents = result.get('agents', [])
        agent_names = ['Curator', 'Researcher', 'Critic', 'Planner', 'Judge']
        
        for idx, agent_name in enumerate(agent_names):
            if idx < len(agents) and agents[idx].get('output'):
                yield f"data: {json.dumps({'type': 'agent', 'agent': agent_name})}\n\n"
                agent_output = agents[idx]['output']
                # Yield full agent output (agents complete sequentially, so we can send full output)
                yield f"data: {json.dumps({'type': 'content', 'content': agent_output})}\n\n"
        
        # Stream final answer
        if result.get('final_answer'):
            yield f"data: {json.dumps({'type': 'agent', 'agent': 'Final'})}\n\n"
            final_output = result['final_answer']
            yield f"data: {json.dumps({'type': 'content', 'content': final_output})}\n\n"
        
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

@app.get("/chat")
async def chat_endpoint(message: str = Query(...)):
    """Streaming SSE endpoint for chat"""
    return StreamingResponse(
        council_stream(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/council")
async def council_endpoint(request: PromptRequest):
    try:
        result = await asyncio.get_event_loop().run_in_executor(None, run_council_sync, request.prompt)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

