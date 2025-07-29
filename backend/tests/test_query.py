import argparse
import json
import logging
from rag_engine import RAGEngine


def main():
    parser = argparse.ArgumentParser(description="Test RAG query for a given client")
    parser.add_argument("--client", required=True, help="Client ID (e.g., john)")
    parser.add_argument("--query", required=True, help="Query string to test")
    parser.add_argument("--meeting", required=False, help="Optional meeting ID to filter")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    
    engine = RAGEngine()
    
    print(f"\n\U0001F50D Querying client '{args.client}' with question: {args.query}\n")
    response = engine.generate_response(
        client_id=args.client,
        query=args.query,
        meeting_id=args.meeting
    )

    print("\n\u2705 Generated Response:")
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()