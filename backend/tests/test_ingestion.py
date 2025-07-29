from backend.rag_engine import RAGEngine

def test_ingestion(client_id: str):
    print(f"\n🔍 Testing ingestion for client: {client_id}")
    engine = RAGEngine()
    success = engine.ingest_client_documents(client_id, force_reprocess=True)

    if success:
        print(f"✅ Ingestion completed for client '{client_id}'.")
        import json
        from pathlib import Path
        
        # After successful ingestion
        debug_path = Path(f"debug_{client_id}_chunks.json")
        if debug_path.exists():
            print(f"\n📄 Debug file found: {debug_path.name}")
            with open(debug_path, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
                for i, chunk in enumerate(chunk_data, start=1):
                    print(f"\n--- Chunk {i} ---")
                    print(f"Chunk ID: {chunk['chunk_id']}")
                    print(f"Content Preview: {chunk['content']}")
                    print(f"Metadata: {json.dumps(chunk['metadata'], indent=2)}")
        else:
            print("\n⚠️ No debug file found — something may have gone wrong.")
    else:
        print(f"❌ Ingestion failed or no new data for client '{client_id}'.")


if __name__ == "__main__":
    test_ingestion("john")  # Replace "john" with any client folder name in /data/clients/