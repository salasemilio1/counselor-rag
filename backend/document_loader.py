import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import uuid
from llm_wrapper import LLMWrapper
from soap_parser import SOAPParser, SOAPContent, SOAPChunk, SOAPSection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MeetingNote:
    """Represents a meeting note document"""
    client_id: str
    meeting_id: str
    date: str
    title: str
    content: str
    file_path: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]

@dataclass 
class DocumentChunk:
    """Represents a chunk of a document"""
    chunk_id: str
    client_id: str
    meeting_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class DocumentLoader:
    """Handles loading and processing of meeting notes for specific clients"""
    
    def __init__(self, data_dir: str = "data", llm_wrapper: Optional[LLMWrapper] = None, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.data_dir = Path(data_dir)
        self.llm_wrapper = llm_wrapper or LLMWrapper()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize SOAP parser
        self.soap_parser = SOAPParser()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Create directory structure
        self._setup_directories()
        
        # Load metadata cache
        self.metadata_cache = self._load_metadata_cache()
    
    def _setup_directories(self):
        """Create necessary directory structure"""
        directories = [
            self.data_dir,
            self.data_dir / "clients",
            self.data_dir / "metadata",
            self.data_dir / "processed"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata_cache(self) -> Dict[str, Any]:
        """Load metadata cache from disk"""
        cache_file = self.data_dir / "metadata" / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata cache: {e}")
                return {}
        return {}
    
    def _save_metadata_cache(self):
        """Save metadata cache to disk"""
        cache_file = self.data_dir / "metadata" / "cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.metadata_cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata cache: {e}")
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Generate hash for file content to detect changes"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"Error generating hash for {file_path}: {e}")
            return ""
    
    def _extract_client_info_from_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """
        Extract client ID and meeting info from filename
        Expected format: clientID_meetingID_YYYY-MM-DD.txt or similar
        You can customize this based on your naming convention
        """
        try:
            # Remove extension
            name_without_ext = filename.rsplit('.', 1)[0]
            
            # Split by underscore
            parts = name_without_ext.split('_')
            
            if len(parts) >= 3:
                client_id = parts[0]
                meeting_id = parts[1]
                date_str = parts[2]
                
                return {
                    'client_id': client_id,
                    'meeting_id': meeting_id,
                    'date': date_str
                }
            else:
                logger.warning(f"Filename {filename} doesn't match expected format")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting info from filename {filename}: {e}")
            return None
    
    def load_single_document(self, file_path: Path, client_id: str = None, meeting_id: str = None) -> Optional[MeetingNote]:
        """Load a single document and create MeetingNote"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                logger.warning(f"Empty file: {file_path}")
                return None
            
            # Extract info from filename if not provided
            filename_info = self._extract_client_info_from_filename(file_path.name)
            
            if not client_id and filename_info:
                client_id = filename_info['client_id']
            if not meeting_id and filename_info:
                meeting_id = filename_info['meeting_id']
            
            if not client_id or not meeting_id:
                logger.error(f"Could not determine client_id or meeting_id for {file_path}")
                return None
            
            # Create meeting note
            meeting_note = MeetingNote(
                client_id=client_id,
                meeting_id=meeting_id,
                date=filename_info['date'] if filename_info else datetime.now().strftime('%Y-%m-%d'),
                title=f"Meeting {meeting_id} - {client_id}",
                content=content,
                file_path=str(file_path),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                metadata={
                    'file_size': file_path.stat().st_size,
                    'file_hash': self._generate_file_hash(file_path),
                    'original_filename': file_path.name
                }
            )
            
            return meeting_note
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return None
    
    def chunk_document(self, meeting_note: MeetingNote) -> List[DocumentChunk]:
        """Split a meeting note into chunks for vector embedding with SOAP awareness"""
        try:
            # First, try SOAP-aware parsing
            soap_content = self.soap_parser.parse_soap_note(meeting_note.content)
            
            if soap_content.is_soap_format:
                logger.info(f"Processing {meeting_note.file_path} as SOAP note")
                return self._create_soap_aware_chunks(meeting_note, soap_content)
            else:
                logger.info(f"Processing {meeting_note.file_path} as unstructured note")
                return self._create_traditional_chunks(meeting_note)
            
        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            # Fallback to traditional chunking
            return self._create_traditional_chunks(meeting_note)
    
    def _create_soap_aware_chunks(self, meeting_note: MeetingNote, soap_content: SOAPContent) -> List[DocumentChunk]:
        """Create chunks from SOAP-structured content"""
        base_metadata = {
            'source_file': meeting_note.file_path,
            'date': meeting_note.date,
            'title': meeting_note.title,
            'client_id': meeting_note.client_id,
            'meeting_id': meeting_note.meeting_id,
            'original_filename': meeting_note.metadata.get('original_filename', Path(meeting_note.file_path).name),
            'document_type': 'soap_note'
        }
        
        # Get SOAP chunks
        soap_chunks = self.soap_parser.create_soap_chunks(soap_content, base_metadata)
        
        # Convert to DocumentChunk format
        document_chunks = []
        for i, soap_chunk in enumerate(soap_chunks):
            chunk = DocumentChunk(
                chunk_id=f"{meeting_note.client_id}_{meeting_note.meeting_id}_soap_{soap_chunk.section_type.value}_{i}",
                client_id=meeting_note.client_id,
                meeting_id=meeting_note.meeting_id,
                content=soap_chunk.content,
                chunk_index=i,
                metadata={
                    **soap_chunk.metadata,
                    'total_chunks': len(soap_chunks),
                    'chunk_type': 'soap_section'
                }
            )
            document_chunks.append(chunk)
        
        return document_chunks
    
    def _create_traditional_chunks(self, meeting_note: MeetingNote) -> List[DocumentChunk]:
        """Create chunks using traditional text splitting"""
        chunks = self.text_splitter.split_text(meeting_note.content)
        
        document_chunks = []
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk(
                chunk_id=f"{meeting_note.client_id}_{meeting_note.meeting_id}_chunk_{i}",
                client_id=meeting_note.client_id,
                meeting_id=meeting_note.meeting_id,
                content=chunk_content,
                chunk_index=i,
                metadata={
                    'source_file': meeting_note.file_path,
                    'date': meeting_note.date,
                    'title': meeting_note.title,
                    'total_chunks': len(chunks),
                    'client_id': meeting_note.client_id,
                    'meeting_id': meeting_note.meeting_id,
                    'original_filename': meeting_note.metadata.get('original_filename', Path(meeting_note.file_path).name),
                    'document_type': 'unstructured_note',
                    'chunk_type': 'text_split'
                }
            )
            document_chunks.append(chunk)
        
        return document_chunks
    
    def process_client_documents(self, client_id: str, force_reprocess: bool = False) -> List[DocumentChunk]:
        """Process all documents for a specific client"""
        client_dir = self.data_dir / "clients" / client_id
        
        if not client_dir.exists():
            logger.warning(f"No directory found for client {client_id}")
            return []
        
        all_chunks = []
        processed_files = []
        
        # Find all text files for the client
        for file_path in client_dir.glob("*.txt"):
            try:
                file_hash = self._generate_file_hash(file_path)
                cache_key = f"{client_id}_{file_path.name}"
                
                # Check if file has been processed and hasn't changed
                if not force_reprocess and cache_key in self.metadata_cache:
                    cached_hash = self.metadata_cache[cache_key].get('file_hash', '')
                    if cached_hash == file_hash:
                        logger.info(f"Skipping {file_path.name} - already processed and unchanged")
                        continue
                
                # Load and process the document
                meeting_note = self.load_single_document(file_path, client_id=client_id)
                if meeting_note:
                    raw_chunks = self.chunk_document(meeting_note)
                    for chunk in raw_chunks:
                        enriched = self.llm_wrapper.summarize_chunk(chunk.content)
                        chunk.metadata.update(enriched)
                    all_chunks.extend(raw_chunks)
                    
                    # Update cache
                    self.metadata_cache[cache_key] = {
                        'file_hash': file_hash,
                        'processed_at': datetime.now().isoformat(),
                        'chunk_count': len(raw_chunks),
                        'meeting_id': meeting_note.meeting_id
                    }
                    
                    processed_files.append(file_path.name)
                    logger.info(f"Processed {file_path.name}: {len(raw_chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        # Save updated cache
        self._save_metadata_cache()
        
        logger.info(f"Processed {len(processed_files)} files for client {client_id}, generated {len(all_chunks)} chunks")
        return all_chunks
    
    def get_client_meetings(self, client_id: str) -> List[Dict[str, str]]:
        """Get list of all meetings for a client"""
        meetings = []
        
        for cache_key, cache_data in self.metadata_cache.items():
            if cache_key.startswith(f"{client_id}_"):
                meetings.append({
                    'meeting_id': cache_data.get('meeting_id', ''),
                    'processed_at': cache_data.get('processed_at', ''),
                    'chunk_count': cache_data.get('chunk_count', 0)
                })
        
        return meetings
    
    def get_all_clients(self) -> List[str]:
        """Get list of all clients with processed documents"""
        clients = set()
        
        for cache_key in self.metadata_cache.keys():
            client_id = cache_key.split('_')[0]
            clients.add(client_id)
        
        return sorted(list(clients))
    
    def add_new_document(self, client_id: str, meeting_id: str, content: str, date: str = None) -> bool:
        """Add a new document programmatically"""
        try:
            # Create client directory if it doesn't exist
            client_dir = self.data_dir / "clients" / client_id
            client_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            filename = f"{client_id}_{meeting_id}_{date}.txt"
            file_path = client_dir / filename
            
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Added new document: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding new document: {e}")
            return False