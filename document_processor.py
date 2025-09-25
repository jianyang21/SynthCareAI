"""
Document Processing for Medical RAG System
Page-level chunking with content hashing for duplicate detection
Optimized for LLaMA 3 8B system
"""

import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import pypdf
from pypdf import PdfReader
from tqdm import tqdm

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Data class for document chunks"""
    text: str
    page_number: int
    source: str
    chunk_hash: str
    chunk_type: str
    metadata: Dict[str, Any]

class DocumentProcessor:
    """
    Document processing for medical PDFs
    Features:
    - Page-level chunking
    - Content deduplication using MD5 hashing
    - Medical text cleaning and normalization
    - Metadata extraction
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize document processor
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            # Default config if not provided
            config = {
                "document": {
                    "chunk_strategy": "page_level",
                    "max_chunk_size": 2000,
                    "chunk_overlap": 200,
                    "min_chunk_size": 100,
                    "use_content_hashing": True,
                    "parallel_processing": True,
                    "max_workers": 8
                },
                "medical": {
                    "domain_keywords": [
                        "hypertension", "blood pressure", "cardiovascular", "treatment",
                        "diagnosis", "medication", "patient", "clinical", "therapy",
                        "symptoms", "systolic", "diastolic", "mmHg", "guidelines"
                    ]
                },
                "paths": {
                    "data_dir": Path("data")
                }
            }
        
        self.config = config["document"]
        self.medical_config = config["medical"]
        self.data_dir = config["paths"]["data_dir"]
        
        # Content hashing for deduplication
        self.chunk_hashes: Set[str] = set()
        self.processed_chunks: List[DocumentChunk] = []
        
        logger.info("📄 Document processor initialized")
        print("📄 Document processor initialized")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        if not text or not text.strip():
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove unwanted characters but preserve medical notation
        text = re.sub(r'[^\w\s.,;:!?()\-\'/°%<>≥≤±]', '', text)
        
        # Preserve medical units and measurements
        # Keep mmHg, mg/kg, etc.
        text = re.sub(r'(\d+)\s*([a-zA-Z]+)', r'\1\2', text)
        
        # Clean up multiple punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[,]{2,}', ',', text)
        
        # Remove excessive line breaks
        text = re.sub(r'\n+', ' ', text)
        
        return text.strip()
    
    def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical entities from text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of extracted medical entities
        """
        entities = {
            "medications": [],
            "measurements": [],
            "conditions": [],
            "procedures": []
        }
        
        text_lower = text.lower()
        
        # Extract blood pressure measurements
        bp_pattern = r'\d+/\d+\s*mmhg'
        measurements = re.findall(bp_pattern, text_lower)
        entities["measurements"].extend(measurements)
        
        # Extract dosages
        dosage_pattern = r'\d+\s*mg(?:/kg|/day|/m2)?'
        dosages = re.findall(dosage_pattern, text_lower)
        entities["medications"].extend(dosages)
        
        # Extract medical keywords
        for keyword in self.medical_config["domain_keywords"]:
            if keyword.lower() in text_lower:
                entities["conditions"].append(keyword)
        
        return entities
    
    def create_chunk_hash(self, text: str) -> str:
        """
        Create MD5 hash for content deduplication
        
        Args:
            text: Text content
            
        Returns:
            MD5 hash string
        """
        normalized_text = self.clean_text(text).lower()
        return hashlib.md5(normalized_text.encode('utf-8')).hexdigest()
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[DocumentChunk]:
        """
        Extract text from PDF with page-level chunking
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of document chunks
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            print(f"❌ PDF not found: {pdf_path}")
            return []
        
        logger.info(f"📄 Processing PDF: {pdf_path.name}")
        print(f"📄 Processing PDF: {pdf_path.name}")
        
        try:
            reader = PdfReader(pdf_path)
            page_chunks = []
            duplicates_found = 0
            
            # Process pages with progress bar
            for page_num, page in enumerate(tqdm(reader.pages, desc="Processing pages")):
                try:
                    # Extract text from page
                    raw_text = page.extract_text()
                    
                    if not raw_text or not raw_text.strip():
                        logger.debug(f"Empty page {page_num + 1}")
                        continue
                    
                    # Clean text
                    cleaned_text = self.clean_text(raw_text)
                    
                    if len(cleaned_text) < self.config["min_chunk_size"]:
                        logger.debug(f"Page {page_num + 1} too short: {len(cleaned_text)} chars")
                        continue
                    
                    # Create content hash
                    chunk_hash = self.create_chunk_hash(cleaned_text)
                    
                    # Check for duplicates
                    if chunk_hash in self.chunk_hashes:
                        duplicates_found += 1
                        logger.debug(f"Duplicate content found on page {page_num + 1}")
                        continue
                    
                    # Extract medical entities
                    medical_entities = self.extract_medical_entities(cleaned_text)
                    
                    # Create chunk metadata
                    metadata = {
                        'file_name': pdf_path.name,
                        'file_size': pdf_path.stat().st_size,
                        'total_pages': len(reader.pages),
                        'word_count': len(cleaned_text.split()),
                        'char_count': len(cleaned_text),
                        'medical_entities': medical_entities
                    }
                    
                    # Create document chunk
                    chunk = DocumentChunk(
                        text=cleaned_text,
                        page_number=page_num + 1,
                        source=str(pdf_path),
                        chunk_hash=chunk_hash,
                        chunk_type='page_level',
                        metadata=metadata
                    )
                    
                    page_chunks.append(chunk)
                    self.chunk_hashes.add(chunk_hash)
                    
                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1}: {e}")
                    continue
            
            logger.info(f"✅ Extracted {len(page_chunks)} unique chunks")
            logger.info(f"📊 Found {duplicates_found} duplicate pages")
            
            print(f"✅ Extracted {len(page_chunks)} unique chunks")
            if duplicates_found > 0:
                print(f"📊 Skipped {duplicates_found} duplicate pages")
            
            self.processed_chunks.extend(page_chunks)
            return page_chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            print(f"❌ Error processing PDF: {e}")
            return []
    
    def process_directory(self, directory: Optional[str] = None) -> List[DocumentChunk]:
        """
        Process all PDFs in a directory
        
        Args:
            directory: Directory path (defaults to configured data directory)
            
        Returns:
            List of all document chunks
        """
        if directory is None:
            directory = self.data_dir
        else:
            directory = Path(directory)
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            print(f"❌ Directory not found: {directory}")
            return []
        
        # Find all PDF files
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            print(f"⚠️  No PDF files found in {directory}")
            return []
        
        logger.info(f"📚 Found {len(pdf_files)} PDF files to process")
        print(f"📚 Found {len(pdf_files)} PDF files to process")
        
        all_chunks = []
        
        # Process each PDF
        for pdf_file in pdf_files:
            logger.info(f"Processing: {pdf_file.name}")
            print(f"Processing: {pdf_file.name}")
            
            chunks = self.extract_text_from_pdf(pdf_file)
            all_chunks.extend(chunks)
        
        logger.info(f"✅ Total chunks processed: {len(all_chunks)}")
        print(f"✅ Total chunks processed: {len(all_chunks)}")
        
        return all_chunks
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics
        
        Returns:
            Dictionary with processing stats
        """
        if not self.processed_chunks:
            return {"error": "No chunks processed yet"}
        
        total_chunks = len(self.processed_chunks)
        total_chars = sum(len(chunk.text) for chunk in self.processed_chunks)
        total_words = sum(chunk.metadata['word_count'] for chunk in self.processed_chunks)
        
        # Medical entity statistics
        all_entities = []
        for chunk in self.processed_chunks:
            entities = chunk.metadata.get('medical_entities', {})
            for entity_type, entity_list in entities.items():
                all_entities.extend(entity_list)
        
        stats = {
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "total_words": total_words,
            "average_chunk_size": total_chars // total_chunks if total_chunks > 0 else 0,
            "unique_hashes": len(self.chunk_hashes),
            "medical_entities_found": len(set(all_entities)),
            "pages_processed": len(set(chunk.page_number for chunk in self.processed_chunks))
        }
        
        return stats

def test_document_processor():
    """Test script for document processor"""
    print("🧪 Testing Document Processor...")
    
    processor = DocumentProcessor()
    
    # Test with data directory
    chunks = processor.process_directory()
    
    if chunks:
        print(f"\n📊 Processing Results:")
        stats = processor.get_processing_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show sample chunk
        print(f"\n📄 Sample chunk:")
        sample = chunks[0]
        print(f"  Page: {sample.page_number}")
        print(f"  Source: {Path(sample.source).name}")
        print(f"  Length: {len(sample.text)} characters")
        print(f"  Preview: {sample.text[:200]}...")
    else:
        print("❌ No documents processed")

if __name__ == "__main__":
    test_document_processor()