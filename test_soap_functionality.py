#!/usr/bin/env python3
"""
Test script to verify SOAP note functionality in the RAG system
"""

import logging
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / "backend"))

from document_loader import DocumentLoader
from rag_engine import RAGEngine
from soap_parser import SOAPParser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_soap_parser():
    """Test SOAP parser functionality"""
    logger.info("Testing SOAP Parser...")
    
    parser = SOAPParser()
    
    # Test with a sample SOAP note
    sample_soap = """
S: Client reports feeling more anxious this week. States "I've been having trouble sleeping."

O: Client appeared restless during session, fidgeting with hands.

A: Client continues to meet criteria for PTSD following motor vehicle accident.

P: 1) Continue weekly therapy sessions
2) Practice deep breathing exercises
"""
    
    soap_content = parser.parse_soap_note(sample_soap)
    logger.info(f"SOAP format detected: {soap_content.is_soap_format}")
    logger.info(f"Subjective content: {soap_content.subjective[:100]}...")
    logger.info(f"Objective content: {soap_content.objective[:100]}...")
    logger.info(f"Assessment content: {soap_content.assessment[:100]}...")
    logger.info(f"Plan content: {soap_content.plan[:100]}...")
    
    # Test query analysis
    test_query = "What did the client report about their anxiety symptoms?"
    query_analysis = parser.enhance_retrieval_query(test_query)
    logger.info(f"Query analysis: {query_analysis}")

def test_document_processing():
    """Test document processing with SOAP awareness"""
    logger.info("Testing Document Processing...")
    
    loader = DocumentLoader("data")
    
    # Test with Eli's new SOAP note
    soap_file = Path("data/clients/eli/eli_003_2025-08-06.txt")
    if soap_file.exists():
        meeting_note = loader.load_single_document(soap_file)
        if meeting_note:
            chunks = loader.chunk_document(meeting_note)
            logger.info(f"Created {len(chunks)} chunks from SOAP note")
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Chunk {i+1}: {chunk.metadata.get('soap_section', 'N/A')} - "
                          f"{chunk.content[:100]}...")

def test_end_to_end_soap_rag():
    """Test end-to-end RAG functionality with SOAP notes"""
    logger.info("Testing End-to-End SOAP RAG...")
    
    try:
        rag_engine = RAGEngine()
        
        # Ingest documents for Eli (includes new SOAP note)
        logger.info("Ingesting Eli's documents...")
        rag_engine.ingest_client_documents("eli", force_reprocess=True)
        
        # Test queries that should benefit from SOAP structure
        test_queries = [
            "What anxiety symptoms did Eli report?",  # Should prioritize Subjective sections
            "What did you observe about Eli's behavior during sessions?",  # Should prioritize Objective
            "What is Eli's current diagnosis?",  # Should prioritize Assessment
            "What homework was assigned to Eli?",  # Should prioritize Plan
            "Tell me about Eli's progress with the accident trauma"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            response = rag_engine.generate_response("eli", query)
            logger.info(f"Answer: {response['answer'][:200]}...")
            logger.info(f"Confidence: {response['confidence']:.2f}")
            logger.info(f"Chunks used: {response['chunks_used']}")
            
            # Log source information
            for source in response['sources'][:2]:  # Show first 2 sources
                logger.info(f"Source: {source.get('filename', 'N/A')} - {source.get('date', 'N/A')}")
    
    except Exception as e:
        logger.error(f"Error in end-to-end test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    logger.info("Starting SOAP Functionality Tests")
    
    print("="*60)
    print("SOAP Note RAG System Test")
    print("="*60)
    
    try:
        test_soap_parser()
        print("\n" + "="*40)
        
        test_document_processing()
        print("\n" + "="*40)
        
        test_end_to_end_soap_rag()
        
        logger.info("All tests completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()