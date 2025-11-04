"""
Parser Service for extracting text from PDF and DOCX files.
"""
import os
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document
from models.schemas import ParsedSection, ParseResult, ChunkData


class ParserService:
    """Service for parsing PDF and DOCX documents."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize the parser service.

        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_pdf(self, filepath: str) -> ParseResult:
        """
        Parse a PDF file and extract text.

        Args:
            filepath: Path to the PDF file

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is corrupted or unreadable
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            reader = PdfReader(filepath)
            sections = []

            # Extract text from each page
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    sections.append(ParsedSection(
                        title=f"Page {page_num}",
                        content=text,
                        page=page_num,
                        order=page_num
                    ))

            # Combine all text
            full_text = '\n\n'.join(section.content for section in sections)

            # Extract metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    'author': reader.metadata.get('/Author', None),
                    'creator': reader.metadata.get('/Creator', None),
                    'producer': reader.metadata.get('/Producer', None),
                    'subject': reader.metadata.get('/Subject', None),
                    'title': reader.metadata.get('/Title', None),
                }

            return ParseResult(
                sections=sections,
                full_text=full_text,
                page_count=len(reader.pages),
                char_count=len(full_text),
                metadata=metadata
            )

        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    def parse_docx(self, filepath: str) -> ParseResult:
        """
        Parse a DOCX file and extract text.

        Args:
            filepath: Path to the DOCX file

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is corrupted or unreadable
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            doc = Document(filepath)
            sections = []
            current_section = ParsedSection(
                title='Introduction',
                content='',
                order=0
            )
            section_order = 0

            # Extract text from paragraphs
            for para in doc.paragraphs:
                # Check if it's a heading
                if para.style.name.startswith('Heading'):
                    # Save current section if it has content
                    if current_section.content.strip():
                        sections.append(current_section)
                        section_order += 1

                    # Start new section
                    current_section = ParsedSection(
                        title=para.text,
                        content='',
                        order=section_order
                    )
                else:
                    # Add paragraph to current section
                    if para.text.strip():
                        current_section.content += para.text + '\n'

            # Add the last section
            if current_section.content.strip():
                sections.append(current_section)

            # If no sections were created (no headings), create one section with all content
            if not sections:
                all_text = '\n'.join(para.text for para in doc.paragraphs if para.text.strip())
                sections.append(ParsedSection(
                    title='Document',
                    content=all_text,
                    order=0
                ))

            # Combine all text
            full_text = '\n\n'.join(section.content for section in sections)

            # Extract metadata from core properties
            metadata = {}
            if doc.core_properties:
                core_props = doc.core_properties
                metadata = {
                    'author': core_props.author,
                    'created': str(core_props.created) if core_props.created else None,
                    'modified': str(core_props.modified) if core_props.modified else None,
                    'title': core_props.title,
                    'subject': core_props.subject,
                }

            return ParseResult(
                sections=sections,
                full_text=full_text,
                paragraph_count=len(doc.paragraphs),
                char_count=len(full_text),
                metadata=metadata
            )

        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {str(e)}")

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[ChunkData]:
        """
        Split text into chunks for RAG processing.

        Uses a sliding window approach with overlap to maintain context.

        Args:
            text: The text to chunk
            metadata: Optional metadata to include with each chunk

        Returns:
            List of ChunkData objects
        """
        if metadata is None:
            metadata = {}

        chunks = []
        text_length = len(text)
        chunk_index = 0

        # Handle empty or very short text
        if text_length == 0:
            return chunks

        if text_length <= self.chunk_size:
            # Text is shorter than chunk size, return as single chunk
            chunks.append(ChunkData(
                content=text.strip(),
                chunk_index=0,
                char_start=0,
                char_end=text_length,
                metadata=metadata
            ))
            return chunks

        # Sliding window chunking with overlap
        start = 0
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk_text = text[start:end]

            # Only add non-empty chunks
            if chunk_text.strip():
                chunks.append(ChunkData(
                    content=chunk_text.strip(),
                    chunk_index=chunk_index,
                    char_start=start,
                    char_end=end,
                    metadata={
                        **metadata,
                        'total_chunks': None,  # Will be set after we know total
                    }
                ))
                chunk_index += 1

            # Move forward by (chunk_size - overlap)
            start += (self.chunk_size - self.chunk_overlap)

            # Prevent infinite loop on edge cases
            if start >= text_length:
                break

        # Update total_chunks in metadata
        for chunk in chunks:
            chunk.metadata['total_chunks'] = len(chunks)

        return chunks

    def parse_file(self, filepath: str) -> ParseResult:
        """
        Parse a file based on its extension.

        Args:
            filepath: Path to the file

        Returns:
            ParseResult with extracted text

        Raises:
            ValueError: If file type is not supported
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.pdf':
            return self.parse_pdf(filepath)
        elif ext in ['.docx', '.doc']:
            return self.parse_docx(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Only .pdf and .docx are supported.")

    def get_file_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        Extract basic file metadata.

        Args:
            filepath: Path to the file

        Returns:
            Dictionary with file metadata
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        stat = os.stat(filepath)
        return {
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'extension': os.path.splitext(filepath)[1].lower(),
            'filename': os.path.basename(filepath),
        }
