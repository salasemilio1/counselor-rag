from fastapi import FastAPI, Request, Query, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import shutil
import logging
import json
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles  # Add this import
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from rag_engine import RAGEngine
from simple_license import SimpleLicenseManager
from datetime import datetime, timedelta
import uuid

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

# Initialize the engine and license manager
# Use parent directory's data folder instead of backend/data
engine = RAGEngine(data_dir="../data", vector_db_path="../data/vector_db")
license_manager = SimpleLicenseManager()

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

class ChatMessage(BaseModel):
    id: str
    type: str  # 'user' or 'ai'
    content: str
    timestamp: str
    sources: Optional[List[dict]] = None

class ChatSession(BaseModel):
    session_id: str
    client_id: str
    title: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str

class SaveChatRequest(BaseModel):
    client_id: str
    session_id: Optional[str] = None
    title: str
    messages: List[dict]

# --- Routes ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/clients")
def list_clients():
    # Check license before listing clients
    can_use, message = license_manager.can_use_feature()
    if not can_use:
        return {"clients": [], "trial_expired": True, "message": message}
    
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
    # Check license before processing query
    can_use, message = license_manager.can_use_feature()
    if not can_use:
        return QueryResponse(
            answer=f"🚫 {message}",
            sources=[],
            confidence=0.0,
            chunks_used=0
        )
    
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

@app.post("/query/stream")
def query_docs_stream(req: QueryRequest):
    """Stream the response for real-time text generation"""
    def generate_stream():
        try:
            # Step 1: Retrieve chunks (same as regular query)
            relevant_chunks = engine.retrieve_relevant_chunks(
                req.client_id, 
                req.query, 
                meeting_ids=req.meeting_ids
            )

            if not relevant_chunks:
                # Send metadata first
                metadata = {
                    "type": "metadata",
                    "sources": [],
                    "confidence": 0.0,
                    "chunks_used": 0
                }
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Send error message
                error_response = {
                    "type": "content",
                    "content": f"I couldn't find anything in the notes that directly relates to '{req.query}'. You might want to check if there are additional session notes to upload, or try rephrasing your question."
                }
                yield f"data: {json.dumps(error_response)}\n\n"
                yield "data: [DONE]\n\n"
                return

            # Step 2: Construct context and prompt
            context = "\n\n".join(chunk['content'] for chunk in relevant_chunks)
            sources = [
                {
                    'meeting_id': chunk['metadata'].get('meeting_id', 'unknown'),
                    'date': chunk['metadata'].get('date', 'unknown'),
                    'chunk_id': chunk['id'],
                    'filename': chunk['metadata'].get('original_filename', chunk['metadata'].get('source_file', '').split('/')[-1] if chunk['metadata'].get('source_file') else 'unknown')
                } for chunk in relevant_chunks
            ]

            # Calculate confidence
            import numpy as np
            avg_similarity = np.mean([
                max(0.0, min(1.0, 1 - chunk.get('distance', 1)))
                for chunk in relevant_chunks
            ])

            # Send metadata first
            metadata = {
                "type": "metadata",
                "sources": sources,
                "confidence": float(avg_similarity),
                "chunks_used": len(relevant_chunks)
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # Step 3: Stream the response
            client_name = req.client_id.capitalize()
            prompt = engine.llm_wrapper.build_structured_prompt(req.query, context, client_name)
            
            for token in engine.llm_wrapper.generate_text_stream(prompt):
                response_data = {
                    "type": "content",
                    "content": token
                }
                yield f"data: {json.dumps(response_data)}\n\n"
            
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("Error in streaming query")
            error_response = {
                "type": "error",
                "content": f"Error processing query: {str(e)}"
            }
            yield f"data: {json.dumps(error_response)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.post("/upload")
async def upload_file(client_id: str = Form(...), files: List[UploadFile] = File(...)):
    """Upload documents for a specific client"""
    # Check license before allowing upload
    can_use, message = license_manager.can_use_feature()
    if not can_use:
        return {"status": "error", "message": message}
    
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
    # Check license before creating client
    can_use, message = license_manager.can_use_feature()
    if not can_use:
        return JSONResponse(status_code=403, content={"status": "error", "message": message})
    
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

@app.get("/clients/{client_id}/documents")
def list_client_documents(client_id: str):
    """Get detailed list of all documents for a client"""
    try:
        client_dir = engine.data_dir / "clients" / client_id
        if not client_dir.exists():
            return {"documents": []}
        
        documents = []
        for file_path in client_dir.glob("*.txt"):
            try:
                stat = file_path.stat()
                # Extract info from filename
                filename_info = engine.document_loader._extract_client_info_from_filename(file_path.name)
                
                documents.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "meeting_id": filename_info.get("meeting_id", "unknown") if filename_info else "unknown",
                    "date": filename_info.get("date", "unknown") if filename_info else "unknown"
                })
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        # Sort by modification time (newest first)
        documents.sort(key=lambda x: x["modified"], reverse=True)
        
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents for {client_id}: {e}")
        return {"documents": [], "error": str(e)}

@app.delete("/clients/{client_id}/documents/{filename}")
def delete_client_document(client_id: str, filename: str):
    """Delete a specific document for a client"""
    try:
        client_dir = engine.data_dir / "clients" / client_id
        file_path = client_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete the file
        file_path.unlink()
        
        # Remove from vector database
        collection = engine._get_client_collection(client_id)
        
        # Find and delete chunks related to this file
        if CHROMA_AVAILABLE:
            try:
                # Get all documents to find ones from this file
                all_data = collection.get(include=["metadatas", "ids"])
                ids_to_delete = []
                
                for i, metadata in enumerate(all_data.get("metadatas", [])):
                    if metadata.get("original_filename") == filename:
                        ids_to_delete.append(all_data["ids"][i])
                
                if ids_to_delete:
                    collection.delete(ids=ids_to_delete)
                    logger.info(f"Deleted {len(ids_to_delete)} chunks for file {filename}")
            except Exception as e:
                logger.error(f"Error removing chunks from vector DB: {e}")
        
        # Update metadata cache
        cache_key = f"{client_id}_{filename}"
        if cache_key in engine.document_loader.metadata_cache:
            del engine.document_loader.metadata_cache[cache_key]
            engine.document_loader._save_metadata_cache()
        
        return {"status": "success", "message": f"Document {filename} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {filename} for {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat management endpoints
@app.post("/chats/save")
def save_chat(request: SaveChatRequest):
    """Save or update a chat session"""
    try:
        chats_dir = engine.data_dir / "chats" / request.client_id
        chats_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if this is an update to existing chat or new chat
        if request.session_id:
            session_id = request.session_id
            chat_file = chats_dir / f"{session_id}.json"
            
            # Load existing data to preserve created_at
            if chat_file.exists():
                with open(chat_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                created_at = existing_data.get('created_at', datetime.now().isoformat())
            else:
                created_at = datetime.now().isoformat()
        else:
            # New chat - generate new session ID
            session_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
        
        # Create chat session
        chat_session = {
            "session_id": session_id,
            "client_id": request.client_id,
            "title": request.title,
            "messages": request.messages,
            "created_at": created_at,
            "updated_at": datetime.now().isoformat()
        }
        
        # Save to file
        chat_file = chats_dir / f"{session_id}.json"
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(chat_session, f, indent=2, default=str)
        
        return {"status": "success", "session_id": session_id}
    
    except Exception as e:
        logger.error(f"Error saving chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{client_id}")
def get_client_chats(client_id: str):
    """Get all chat sessions for a client"""
    try:
        chats_dir = engine.data_dir / "chats" / client_id
        if not chats_dir.exists():
            return {"chats": []}
        
        chats = []
        for chat_file in chats_dir.glob("*.json"):
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    
                # Clean up old chats based on settings (default 7 days)
                created_at = datetime.fromisoformat(chat_data.get('created_at', datetime.now().isoformat()))
                if datetime.now() - created_at > timedelta(days=7):  # TODO: Make configurable
                    chat_file.unlink()  # Delete old chat
                    continue
                    
                # Add summary info
                chats.append({
                    "session_id": chat_data["session_id"],
                    "title": chat_data["title"],
                    "created_at": chat_data["created_at"],
                    "updated_at": chat_data["updated_at"],
                    "message_count": len(chat_data.get("messages", []))
                })
            except Exception as e:
                logger.error(f"Error loading chat file {chat_file}: {e}")
                continue
        
        # Sort by updated time (newest first)
        chats.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return {"chats": chats}
    
    except Exception as e:
        logger.error(f"Error getting chats for {client_id}: {e}")
        return {"chats": [], "error": str(e)}

@app.get("/chats/{client_id}/{session_id}")
def get_chat_session(client_id: str, session_id: str):
    """Get a specific chat session"""
    try:
        chat_file = engine.data_dir / "chats" / client_id / f"{session_id}.json"
        
        if not chat_file.exists():
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        with open(chat_file, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
        
        return chat_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session {session_id} for {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chats/{client_id}/{session_id}")
def delete_chat_session(client_id: str, session_id: str):
    """Delete a specific chat session"""
    try:
        chat_file = engine.data_dir / "chats" / client_id / f"{session_id}.json"
        
        if not chat_file.exists():
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        chat_file.unlink()
        return {"status": "success", "message": "Chat session deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session {session_id} for {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- License Management Endpoints ---
@app.get("/license/status")
def get_license_status():
    """Get current license/trial status"""
    try:
        status = license_manager.get_trial_status()
        # Add user-friendly message
        status['message'] = license_manager.get_trial_message()
        return status
    except Exception as e:
        logger.error(f"Error getting license status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":  # Fixed the syntax error
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)