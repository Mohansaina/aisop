import re
import os
from typing import Dict, List, Any, Tuple
from pypdf import PdfReader

class DocumentService:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts text page-by-page from a PDF and returns the full text
        along with page metadata.
        """
        reader = PdfReader(file_path)
        full_text = []
        page_mappings = []
        
        char_count = 0
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            # Clean basic page headers/footers if necessary
            text_cleaned = DocumentService.clean_text(text)
            full_text.append(text_cleaned)
            
            start_idx = char_count
            char_count += len(text_cleaned) + 1  # +1 for join newline
            end_idx = char_count
            
            page_mappings.append({
                "page_number": i + 1,
                "start_char": start_idx,
                "end_char": end_idx
            })
            
        return "\n".join(full_text), page_mappings

    @staticmethod
    def extract_text_from_markdown(file_path: str) -> Tuple[str, Dict[str, str]]:
        """
        Reads a markdown file, parses the cover page metadata table, 
        and returns clean text and metadata dictionary.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        metadata = {}
        # Simple cover page regex parser
        # Example: | **Document Title** | Food Safety Standard Operating Procedure |
        matches = re.findall(r"\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|\n]+?)\s*\|", content)
        for key, value in matches:
            clean_key = key.strip().lower().replace(" ", "_")
            metadata[clean_key] = value.strip()
            
        return content, metadata

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalizes spacing, removes redundant line breaks, and sanitizes characters.
        """
        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t]+", " ", text)
        # Normalize double newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = 1000, 
        overlap: int = 200, 
        page_mappings: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunks document text semantically, seeking paragraph boundaries (e.g. double newlines) 
        and resolving page numbers.
        """
        chunks = []
        paragraphs = text.split("\n\n")
        
        current_chunk = []
        current_length = 0
        chunk_idx = 0
        char_offset = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_len = len(para)
            
            # If a single paragraph is larger than chunk_size, split by sentences
            if para_len > chunk_size:
                sentences = re.split(r"(?<=[.!?]) +", para)
                for sentence in sentences:
                    sentence_len = len(sentence)
                    if current_length + sentence_len > chunk_size and current_chunk:
                        # Flush current chunk
                        chunk_text = " ".join(current_chunk)
                        chunks.append({
                            "chunk_number": chunk_idx,
                            "text": chunk_text,
                            "section": DocumentService.detect_section(chunk_text),
                            "page_number": DocumentService.get_page_number(char_offset, page_mappings)
                        })
                        chunk_idx += 1
                        # Retain overlap
                        overlap_words = []
                        overlap_len = 0
                        for word in reversed(current_chunk):
                            if overlap_len + len(word) < overlap:
                                overlap_words.insert(0, word)
                                overlap_len += len(word)
                            else:
                                break
                        current_chunk = overlap_words
                        current_length = sum(len(w) for w in current_chunk) + len(current_chunk)
                    
                    current_chunk.append(sentence)
                    current_length += sentence_len
            else:
                if current_length + para_len > chunk_size and current_chunk:
                    # Flush current chunk
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append({
                        "chunk_number": chunk_idx,
                        "text": chunk_text,
                        "section": DocumentService.detect_section(chunk_text),
                        "page_number": DocumentService.get_page_number(char_offset, page_mappings)
                    })
                    chunk_idx += 1
                    # Keep overlap
                    overlap_paras = []
                    overlap_len = 0
                    for p in reversed(current_chunk):
                        if overlap_len + len(p) < overlap:
                            overlap_paras.insert(0, p)
                            overlap_len += len(p)
                        else:
                            break
                    current_chunk = overlap_paras
                    current_length = sum(len(p) for p in current_chunk) + len(current_chunk)
                
                current_chunk.append(para)
                current_length += para_len
            
            char_offset += para_len + 2 # +2 for double newlines
            
        # Add remaining text
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "chunk_number": chunk_idx,
                "text": chunk_text,
                "section": DocumentService.detect_section(chunk_text),
                "page_number": DocumentService.get_page_number(char_offset, page_mappings)
            })
            
        return chunks

    @staticmethod
    def detect_section(chunk_text: str) -> str:
        """
        Tries to locate section headings (e.g. ## Heading) within the chunk text.
        """
        match = re.search(r"^(?:#+)\s*(.+)$", chunk_text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        # Fallback to standard SOP section indicator
        match = re.search(r"##\s*(\d+\.\s*[^\n]+)", chunk_text)
        if match:
            return match.group(1).strip()
        return "General"

    @staticmethod
    def get_page_number(char_offset: int, page_mappings: List[Dict[str, Any]] = None) -> int:
        """
        Determines the PDF page number associated with a char offset index.
        """
        if not page_mappings:
            return 1
        for mapping in page_mappings:
            if mapping["start_char"] <= char_offset <= mapping["end_char"]:
                return mapping["page_number"]
        return page_mappings[-1]["page_number"] if page_mappings else 1
