from fastapi import FastAPI, Request, Query, HTTPException, UploadFile, File, Form
import shutil
import logging
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles  # Add this import
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from rag_engine import RAGEngine

logger = logging.getLogger(__name__)

app = FastAPI()

# CORS config for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the engine
engine = RAGEngine()

# Mount static files for document serving
app.mount("/static", StaticFiles(directory=str(engine.data_dir)), name="static")

# --- Request/Response Models ---
class QueryRequest(BaseModel):
    client_id: str
    query: str
    meeting_ids: Optional[List[str]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: float
    chunks_used: int

class NewClientRequest(BaseModel):
    client_id: str

# --- Routes ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/clients")
def list_clients():
    try:
        clients_dir = engine.data_dir / "clients"
        if not clients_dir.exists():
            return {"clients": []}
        
        clients = [d.name for d in clients_dir.glob("*") if d.is_dir()]
        return {"clients": clients}
    except Exception as e:
        return {"clients": [], "error": str(e)}

@app.get("/meetings/{client_id}")
def get_meetings(client_id: str):
    try:
        summary = engine.get_client_summary(client_id)
        # Ensure consistent response structure
        return {
            "meetings": summary.get("meetings", []),
            "files": summary.get("files", []),
            "client_id": client_id
        }
    except Exception as e:
        return {"meetings": [], "files": [], "error": str(e)}

@app.post("/query", response_model=QueryResponse)
def query_docs(req: QueryRequest):
    try:
        result = engine.generate_response(
            client_id=req.client_id,
            query=req.query,
            meeting_ids=req.meeting_ids
        )
        return result
    except Exception as e:
        return QueryResponse(
            answer=f"Error processing query: {str(e)}",
            sources=[],
            confidence=0.0,
            chunks_used=0
        )

@app.post("/upload")
async def upload_file(client_id: str = Form(...), files: List[UploadFile] = File(...)):
    """Upload documents for a specific client"""
    try:
        upload_dir = engine.data_dir / "clients" / client_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            uploaded_files.append(file.filename)
        
        return {"status": "success", "uploaded_files": uploaded_files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/ingest/{client_id}")
def ingest_documents(client_id: str, force: bool = False):
    """Trigger ingestion for a client's documents"""
    try:
        success = engine.ingest_client_documents(client_id, force_reprocess=force)
        if success: 
            return {"status": "success"}
        else: 
            return JSONResponse(status_code=400, content={
                "status": "no_data",
                "message": f"No new chunks to ingest for client '{client_id}'."
            })
    except Exception as e:
        logger.exception(f"Ingestion error for {client_id}")
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": str(e)
        })

@app.get("/debug_chunks/{client_id}")
def get_debug_chunks(client_id: str):
    """Return debug chunk metadata for inspection"""
    try:
        debug_file = engine.data_dir / f"debug_{client_id}_chunks.json"
        if debug_file.exists():
            import json
            with open(debug_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return content
        return {"error": "Debug file not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/clients/create")
def create_client(req: NewClientRequest):
    """Create a new client directory and initialize metadata"""
    client_id = req.client_id.lower().replace(" ", "_")
    client_dir = engine.data_dir / "clients" / client_id
    try:
        # Create the directory if it doesn't exist yet
        client_dir.mkdir(parents=True, exist_ok=True)
        # Optionally initialize cache or metadata
        return {"status": "success", "client_id": client_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/clients/{client_id}/reset")
def reset_client_data(client_id: str):
    """Delete all ingested vectors for a client."""
    try:
        collection = engine._get_client_collection(client_id)
        # Retrieve all existing IDs
        existing = collection.get(include=["ids"])
        all_ids = existing.get("ids", [])
        if all_ids:
            collection.delete(ids=all_ids)
        return {"status": "success", "deleted": len(all_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":  # Fixed the syntax error
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)