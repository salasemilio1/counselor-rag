

@app.post("/upload-document")
async def upload_document(client_id: str = Form(...), file: UploadFile = File(...)):
    # Save file to data/clients/<client_id>/
    # Extract meeting_id and date (or auto-generate)
    # Return success/failure

@app.post("/ingest/{client_id}")
def ingest_client_documents(client_id: str):
    # Calls engine.ingest_client_documents(client_id)