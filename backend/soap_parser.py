import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SOAPSection(Enum):
    """SOAP note sections"""
    SUBJECTIVE = "subjective"
    OBJECTIVE = "objective"
    ASSESSMENT = "assessment"
    PLAN = "plan"
    UNSTRUCTURED = "unstructured"

@dataclass
class SOAPContent:
    """Represents parsed SOAP note content"""
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""
    unstructured: str = ""
    is_soap_format: bool = False
    
    def get_section_content(self, section: SOAPSection) -> str:
        """Get content for a specific SOAP section"""
        if section == SOAPSection.SUBJECTIVE:
            return self.subjective
        elif section == SOAPSection.OBJECTIVE:
            return self.objective
        elif section == SOAPSection.ASSESSMENT:
            return self.assessment
        elif section == SOAPSection.PLAN:
            return self.plan
        else:
            return self.unstructured

@dataclass
class SOAPChunk:
    """Represents a chunk from a SOAP note with enhanced metadata"""
    content: str
    section_type: SOAPSection
    section_content_full: str  # Full content of the section this chunk came from
    metadata: Dict[str, Any]

class SOAPParser:
    """Parser for SOAP notes with flexible detection"""
    
    def __init__(self):
        # Common SOAP section patterns - flexible to handle variations
        self.soap_patterns = {
            SOAPSection.SUBJECTIVE: [
                r'(?i)^s\s*[:|-]?\s*(.*?)(?=^[oa][:|-]|$)',
                r'(?i)^subjective\s*[:|-]?\s*(.*?)(?=^(?:objective|assessment)[:|-]|$)',
                r'(?i)(?:^|\n)\s*subjective\s*[:|-]?\s*(.*?)(?=(?:\n\s*(?:objective|assessment)|$))',
                r'(?i)client\s+(?:reports?|states?|says?)\s+(.*?)(?=\n\s*(?:observed?|assessment|plan)|$)',
            ],
            SOAPSection.OBJECTIVE: [
                r'(?i)^o\s*[:|-]?\s*(.*?)(?=^[ap][:|-]|$)',
                r'(?i)^objective\s*[:|-]?\s*(.*?)(?=^(?:assessment|plan)[:|-]|$)',
                r'(?i)(?:^|\n)\s*objective\s*[:|-]?\s*(.*?)(?=(?:\n\s*(?:assessment|plan)|$))',
                r'(?i)(?:observed?|during\s+session)\s*(.*?)(?=\n\s*(?:assessment|plan)|$)',
            ],
            SOAPSection.ASSESSMENT: [
                r'(?i)^a\s*[:|-]?\s*(.*?)(?=^p[:|-]|$)',
                r'(?i)^assessment\s*[:|-]?\s*(.*?)(?=^plan[:|-]|$)',
                r'(?i)(?:^|\n)\s*assessment\s*[:|-]?\s*(.*?)(?=(?:\n\s*plan|$))',
                r'(?i)(?:diagnosis|impression|clinical\s+opinion)\s*[:|-]?\s*(.*?)(?=\n\s*plan|$)',
            ],
            SOAPSection.PLAN: [
                r'(?i)^p\s*[:|-]?\s*(.*)',
                r'(?i)^plan\s*[:|-]?\s*(.*)',
                r'(?i)(?:^|\n)\s*plan\s*[:|-]?\s*(.*)',
                r'(?i)(?:intervention|treatment|homework|next\s+steps?)\s*[:|-]?\s*(.*)',
            ]
        }
        
        # Keywords that indicate SOAP-like content
        self.soap_indicators = {
            'subjective_keywords': ['client reports', 'client states', 'patient says', 'reports feeling', 'described', 'expressed'],
            'objective_keywords': ['observed', 'during session', 'appeared', 'demonstrated', 'exhibited', 'noted'],
            'assessment_keywords': ['diagnosis', 'assessment', 'impression', 'clinical opinion', 'meets criteria', 'symptoms indicate'],
            'plan_keywords': ['homework', 'intervention', 'treatment plan', 'next session', 'goals', 'recommended', 'follow-up']
        }
    
    def detect_soap_format(self, text: str) -> bool:
        """Detect if text follows SOAP format (strict or loose)"""
        text_lower = text.lower()
        
        # Check for explicit SOAP headers
        explicit_headers = sum([
            1 for pattern in [r'(?i)\bs\s*[:|-]', r'(?i)\bsubjective\s*[:|-]', 
                            r'(?i)\bo\s*[:|-]', r'(?i)\bobjective\s*[:|-]',
                            r'(?i)\ba\s*[:|-]', r'(?i)\bassessment\s*[:|-]',
                            r'(?i)\bp\s*[:|-]', r'(?i)\bplan\s*[:|-]']
            if re.search(pattern, text)
        ])
        
        if explicit_headers >= 2:
            return True
        
        # Check for SOAP-like keywords indicating structured content
        keyword_score = 0
        for category, keywords in self.soap_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                keyword_score += 1
        
        # Consider it SOAP-like if it has keywords from at least 2 categories
        return keyword_score >= 2
    
    def parse_soap_note(self, text: str) -> SOAPContent:
        """Parse text into SOAP sections with flexible matching"""
        soap_content = SOAPContent()
        
        # Check if this looks like a SOAP note
        soap_content.is_soap_format = self.detect_soap_format(text)
        
        if not soap_content.is_soap_format:
            soap_content.unstructured = text
            return soap_content
        
        # Try to extract each SOAP section
        remaining_text = text
        sections_found = {}
        
        for section, patterns in self.soap_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
                if matches:
                    content = matches[0].strip() if isinstance(matches[0], str) else ' '.join(matches[0]).strip()
                    if content and len(content) > 10:  # Avoid very short matches
                        sections_found[section] = content
                        break
        
        # Assign found sections
        soap_content.subjective = sections_found.get(SOAPSection.SUBJECTIVE, "")
        soap_content.objective = sections_found.get(SOAPSection.OBJECTIVE, "")
        soap_content.assessment = sections_found.get(SOAPSection.ASSESSMENT, "")
        soap_content.plan = sections_found.get(SOAPSection.PLAN, "")
        
        # If no structured sections found but it looks like SOAP, treat as unstructured
        if not any([soap_content.subjective, soap_content.objective, 
                   soap_content.assessment, soap_content.plan]):
            soap_content.unstructured = text
        
        logger.info(f"SOAP parsing results: S={len(soap_content.subjective)}, "
                   f"O={len(soap_content.objective)}, A={len(soap_content.assessment)}, "
                   f"P={len(soap_content.plan)}, Unstructured={len(soap_content.unstructured)}")
        
        return soap_content
    
    def create_soap_chunks(self, soap_content: SOAPContent, base_metadata: Dict) -> List[SOAPChunk]:
        """Create chunks from SOAP content with enhanced metadata"""
        chunks = []
        
        if not soap_content.is_soap_format:
            # Handle as unstructured content
            chunk = SOAPChunk(
                content=soap_content.unstructured,
                section_type=SOAPSection.UNSTRUCTURED,
                section_content_full=soap_content.unstructured,
                metadata={
                    **base_metadata,
                    'soap_section': SOAPSection.UNSTRUCTURED.value,
                    'is_soap_format': False,
                    'section_summary': self._create_section_summary(soap_content.unstructured)
                }
            )
            chunks.append(chunk)
            return chunks
        
        # Process each SOAP section
        sections_to_process = [
            (SOAPSection.SUBJECTIVE, soap_content.subjective),
            (SOAPSection.OBJECTIVE, soap_content.objective),
            (SOAPSection.ASSESSMENT, soap_content.assessment),
            (SOAPSection.PLAN, soap_content.plan)
        ]
        
        for section_type, content in sections_to_process:
            if content and content.strip():
                # For longer sections, we might want to split further
                # For now, keep each section as one chunk for semantic coherence
                section_chunks = self._chunk_section_content(content, section_type, base_metadata)
                chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_section_content(self, content: str, section_type: SOAPSection, base_metadata: Dict) -> List[SOAPChunk]:
        """Create chunks from a single SOAP section"""
        # For most SOAP sections, keep as single chunk to maintain context
        # Only split if very long (>800 chars)
        if len(content) <= 800:
            chunk = SOAPChunk(
                content=content,
                section_type=section_type,
                section_content_full=content,
                metadata={
                    **base_metadata,
                    'soap_section': section_type.value,
                    'is_soap_format': True,
                    'section_summary': self._create_section_summary(content),
                    'section_length': len(content)
                }
            )
            return [chunk]
        
        # Split longer sections while maintaining sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', content)
        sub_chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= 600:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunk = SOAPChunk(
                        content=current_chunk.strip(),
                        section_type=section_type,
                        section_content_full=content,
                        metadata={
                            **base_metadata,
                            'soap_section': section_type.value,
                            'is_soap_format': True,
                            'section_summary': self._create_section_summary(current_chunk),
                            'section_length': len(current_chunk),
                            'is_partial_section': True
                        }
                    )
                    sub_chunks.append(chunk)
                current_chunk = sentence + " "
        
        # Add remaining content
        if current_chunk.strip():
            chunk = SOAPChunk(
                content=current_chunk.strip(),
                section_type=section_type,
                section_content_full=content,
                metadata={
                    **base_metadata,
                    'soap_section': section_type.value,
                    'is_soap_format': True,
                    'section_summary': self._create_section_summary(current_chunk),
                    'section_length': len(current_chunk),
                    'is_partial_section': True
                }
            )
            sub_chunks.append(chunk)
        
        return sub_chunks
    
    def _create_section_summary(self, content: str) -> str:
        """Create a brief summary of section content for metadata"""
        words = content.split()
        if len(words) <= 20:
            return content
        
        # Return first 15 words + "..."
        return ' '.join(words[:15]) + "..."
    
    def enhance_retrieval_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine which SOAP sections are most relevant"""
        query_lower = query.lower()
        
        # Keywords that suggest specific SOAP sections
        section_weights = {
            SOAPSection.SUBJECTIVE: 1.0,
            SOAPSection.OBJECTIVE: 1.0,
            SOAPSection.ASSESSMENT: 1.0,
            SOAPSection.PLAN: 1.0
        }
        
        # Boost sections based on query keywords
        if any(keyword in query_lower for keyword in ['client said', 'reported', 'expressed', 'feels', 'feeling']):
            section_weights[SOAPSection.SUBJECTIVE] = 1.5
        
        if any(keyword in query_lower for keyword in ['observed', 'behavior', 'appeared', 'during session']):
            section_weights[SOAPSection.OBJECTIVE] = 1.5
            
        if any(keyword in query_lower for keyword in ['diagnosis', 'assessment', 'clinical', 'symptoms', 'criteria']):
            section_weights[SOAPSection.ASSESSMENT] = 1.5
            
        if any(keyword in query_lower for keyword in ['homework', 'plan', 'intervention', 'goals', 'next steps']):
            section_weights[SOAPSection.PLAN] = 1.5
        
        return {
            'section_weights': section_weights,
            'enhanced_keywords': self._extract_clinical_keywords(query)
        }
    
    def _extract_clinical_keywords(self, query: str) -> List[str]:
        """Extract clinical/therapeutic keywords from query"""
        clinical_terms = [
            'anxiety', 'depression', 'trauma', 'ptsd', 'therapy', 'counseling',
            'coping', 'stress', 'breakthrough', 'progress', 'setback', 'goals',
            'relationship', 'family', 'work', 'career', 'emotional', 'feelings',
            'mindfulness', 'homework', 'assignment', 'intervention', 'session'
        ]
        
        query_lower = query.lower()
        return [term for term in clinical_terms if term in query_lower]