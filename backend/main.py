from fastapi import FastAPI, Request, Query
from fastapi import UploadFile, File, Form
import shutil
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from rag_engine import RAGEngine

app = FastAPI()

# CORS config for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the engine
engine = RAGEngine()

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

# --- Routes ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/clients")
def list_clients():
    # In production, load from client registry
    return {"clients": [d.name for d in engine.data_dir.glob("clients/*") if d.is_dir()]}

@app.get("/meetings/{client_id}")
def get_meetings(client_id: str):
    summary = engine.get_client_summary(client_id)
    return summary

@app.post("/query", response_model=QueryResponse)
def query_docs(req: QueryRequest):
    result = engine.generate_response(
        client_id=req.client_id,
        query=req.query,
        meeting_ids=req.meeting_ids
    )
    return result


# --- New Routes ---

@app.post("/upload")
async def upload_file(client_id: str = Form(...), files: List[UploadFile] = File(...)):
    """Upload documents for a specific client"""
    upload_dir = engine.data_dir / "clients" / client_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

    return {"status": "success", "uploaded_files": [file.filename for file in files]}


@app.post("/ingest/{client_id}")
def ingest_documents(client_id: str, force: bool = False):
    """Trigger ingestion for a client's documents"""
    success = engine.ingest_client_documents(client_id, force_reprocess=force)
    return {"status": "success" if success else "skipped or failed"}


@app.get("/debug_chunks/{client_id}")
def get_debug_chunks(client_id: str):
    """Return debug chunk metadata for inspection"""
    debug_file = engine.data_dir / f"debug_{client_id}_chunks.json"
    if debug_file.exists():
        return JSONResponse(content=debug_file.read_text(encoding="utf-8"))
    return JSONResponse(status_code=404, content={"error": "Debug file not found"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
