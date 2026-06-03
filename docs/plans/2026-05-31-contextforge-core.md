# ContextForge Core Context Optimization Engine

> **For Claude / Antigravity:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the production-ready core differentiator for ContextForge: a highly performant, type-safe, and asynchronous Python-based Context Optimization Engine. It normalizes heterogeneous files (PDF, DOCX, PPTX, Images) into structured GFM Markdown, semantically chunks the content, prunes redundant text to maximize LLM token efficiency, extracts entities/metadata, and compiles them into a unified "AI Context Package" available via a robust FastAPI service.

**Architecture:** We use Domain-Driven Design (DDD) with clean architectural boundaries. 
- **Core Domain**: Defines document schemas, normalization entities, chunk structures, and token metrics.
- **Service Layer**: Orchestrates file ingestion, parsing, chunking, and AI-powered visual OCR or summarization.
- **Adapter/Infrastructure Layer**: Implements third-party libraries (`pymupdf`, `python-docx`, `python-pptx`, `google-genai` for Gemini API).
- **Presentation Layer**: Exposes asynchronous REST endpoints using FastAPI and a beautiful command-line tool.

```mermaid
graph TD
    A[Input Document] --> B[FastAPI / CLI Presentation Layer]
    B --> C[Service Orchestrator]
    C --> D[Ingestion & In-Memory Stream Buffer]
    
    subgraph Processing Pipeline
        D --> E[Normalization Service]
        E --> E1[PyMuPDF / docx / pptx Parsers]
        E --> E2[AI Vision Page Analyzer]
        
        E1 & E2 --> F[Token Compression Engine]
        F --> F1[Redundancy Pruning]
        F --> F2[Hierarchical Preservation]
        
        F1 & F2 --> G[Semantic Chunker & Entity Extractor]
        G --> H[Context Package Compiler]
    end
    
    H --> I[Output Context Package: Markdown, JSON Chunks, Entities, Savings Stats]
```

**Tech Stack:**
- **Language**: Python 3.12+ (fully typed)
- **Framework**: FastAPI (asynchronous ASGI)
- **Local Parsing**: `pymupdf` (PyMuPDF), `python-docx`, `python-pptx`
- **AI/OCR**: `google-genai` (with the official Gemini 2.5 Flash SDK)
- **Tokenization**: `tiktoken` (for token estimation)
- **Validation**: `pydantic` v2 (for strict type validation)
- **Config**: `python-dotenv`
- **Testing**: `pytest` + `pytest-asyncio`

---

## Code Generation Quality Gate (Bug Prevention Workflow)
Before generating code for any task in this plan, the executing agent must rigorously follow and document these 11 steps:
1. **Analyze requirements**: Extract specifications, data inputs, and expected behaviors.
2. **Identify edge cases**: Document failure states, empty strings, massive files, missing keys, timeout scenarios.
3. **Create implementation plan**: Structure classes, helper methods, and API definitions.
4. **Design tests first**: Specify how to verify success using isolated pytest fixtures.
5. **Generate code**: Produce fully typed, production-ready code with comprehensive error catching and logging.
6. **Run static analysis mentally**: Trace imports, data boundaries, and function signatures.
7. **Check for security issues**: Validate input boundaries, strip potentially malicious payloads, handle API keys safely.
8. **Check for performance issues**: Avoid blocking operations in async calls, use streaming where possible, minimize RAM copies of large strings.
9. **Check for type errors**: Verify strict type hints and Pydantic models.
10. **Verify imports and dependencies**: Confirm modules are correctly linked.
11. **Produce final code only after validation**.

---

## Part 1: Project Initialization & Core Domain Models

### Task 1: Environment and Core Infrastructure Setup
**Files:**
- Create: `D:\TK\pyproject.toml`
- Create: `D:\TK\requirements.txt`
- Create: `D:\TK\.env`

**Step 1: Write requirements.txt**
Define the exact library versions for standard document parsing, AI connections, CLI, and test frameworks.

`D:\TK\requirements.txt` contents:
```text
fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.4
python-dotenv>=1.0.1
pymupdf>=1.24.0
python-docx>=1.1.0
python-pptx>=0.6.23
google-genai>=0.2.0
tiktoken>=0.6.0
rich>=13.7.0
pytest>=8.1.1
pytest-asyncio>=0.23.6
httpx>=0.27.0
```

`D:\TK\.env` contents:
```ini
# Core Configuration for ContextForge
GEMINI_API_KEY=AIzaSyAmJl5XqVbMjvasCmsHOxFORVnOjbjQ-OM
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Step 2: Initialize Git Repository & Core Directory Structure**
Run the shell commands in `D:\TK` to set up git, directories, and virtual environment.

Run in terminal:
```powershell
cd D:\TK
git init
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
mkdir contextforge/core
mkdir contextforge/services
mkdir contextforge/adapters
mkdir contextforge/api
mkdir tests
```
Expected: Python virtual environment successfully created and libraries installed.

**Step 3: Commit Scaffolding**
```bash
git add requirements.txt .env
git commit -m "chore: initialize ContextForge workspace scaffolding and dependencies"
```

---

### Task 2: Core Domain Model Definitions
Design type-safe Pydantic models to represent processed document structures, parsed pages, tables, extracted entities, and the final optimized context packages.

**Files:**
- Create: `D:\TK\contextforge/core/models.py`
- Create: `D:\TK\tests/test_models.py`

**Step 1: Write Core Domain Models**
Create standard, fully typed validation structures inside `D:\TK\contextforge/core/models.py`:
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ExtractedTable(BaseModel):
    headers: List[str]
    rows: List[List[str]]
    markdown_representation: str

class ExtractedEntity(BaseModel):
    name: str = Field(description="Name of the entity extracted")
    category: str = Field(description="Category (e.g. Person, Org, Location, Date)")
    context: str = Field(description="Snippet showing the entity context")

class DocumentPage(BaseModel):
    page_number: int
    text_content: str
    headings: List[str] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    raw_size_bytes: int

class TokenMetrics(BaseModel):
    raw_tokens_estimate: int
    compressed_tokens: int
    tokens_saved: int
    savings_percentage: float

class AIContextPackage(BaseModel):
    document_name: str
    metadata: Dict[str, str] = Field(default_factory=dict)
    full_markdown: str
    entities: List[ExtractedEntity] = Field(default_factory=list)
    chunks: List[str] = Field(default_factory=list)
    metrics: TokenMetrics
```

**Step 2: Write Models Unit Test**
Create `D:\TK\tests/test_models.py` to verify schema validation and constraint checking.
```python
import pytest
from contextforge.core.models import ExtractedTable, TokenMetrics, AIContextPackage

def test_token_metrics_calculation():
    metrics = TokenMetrics(
        raw_tokens_estimate=1000,
        compressed_tokens=400,
        tokens_saved=600,
        savings_percentage=60.0
    )
    assert metrics.tokens_saved == 600
    assert metrics.savings_percentage == 60.0

def test_extracted_table_serialization():
    table = ExtractedTable(
        headers=["Name", "Score"],
        rows=[["Alice", "95"], ["Bob", "90"]],
        markdown_representation="| Name | Score |\n|---|---|\n| Alice | 95 |\n| Bob | 90 |"
    )
    assert len(table.headers) == 2
    assert "Alice" in table.markdown_representation
```

**Step 3: Run Tests**
Run: `pytest tests/test_models.py -v`
Expected: PASS

**Step 4: Commit**
```bash
git add contextforge/core/models.py tests/test_models.py
git commit -m "feat: design core Pydantic domain models for ContextForge"
```

---

## Part 2: High-Performance Normalization Adapters

### Task 3: Local Formats Normalization Service (PDF, DOCX, PPTX)
We will build a high-performance local normalization engine. We'll use modern libraries to extract structured layouts, tables, slide sections, and notes.

**Files:**
- Create: `D:\TK\contextforge/adapters/local_parsers.py`
- Create: `D:\TK\tests/test_local_parsers.py`

**Step 1: Write Local Parser Adapters**
Create `D:\TK\contextforge/adapters/local_parsers.py`:
```python
from pathlib import Path
import fitz # PyMuPDF
import docx
from pptx import Presentation
from typing import List
from contextforge.core.models import DocumentPage, ExtractedTable

class LocalDocumentParser:
    """Orchestrates local high-performance file parsing."""
    
    @staticmethod
    def parse_pdf(filepath: Path) -> List[DocumentPage]:
        doc = fitz.open(str(filepath))
        pages = []
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                
                # Table Extraction using PyMuPDF finder
                extracted_tables = []
                tabs = page.find_tables()
                for tab in tabs:
                    data = tab.extract()
                    if data and len(data) > 0:
                        headers = [str(h or "") for h in data[0]]
                        rows = [[str(cell or "") for cell in r] for r in data[1:]]
                        # Build Markdown Table
                        md_table = "| " + " | ".join(headers) + " |\n"
                        md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                        for r in rows:
                            md_table += "| " + " | ".join(r) + " |\n"
                        extracted_tables.append(ExtractedTable(
                            headers=headers,
                            rows=rows,
                            markdown_representation=md_table.strip()
                        ))
                
                pages.append(DocumentPage(
                    page_number=page_num + 1,
                    text_content=text,
                    tables=extracted_tables,
                    raw_size_bytes=len(text.encode("utf-8"))
                ))
        finally:
            doc.close()
        return pages

    @staticmethod
    def parse_docx(filepath: Path) -> List[DocumentPage]:
        doc = docx.Document(str(filepath))
        text_lines = []
        tables = []
        
        # Sequentially parse body paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                text_lines.append(text)
                
        # Parse tables
        for t in doc.tables:
            if not t.rows:
                continue
            headers = [cell.text.strip() for cell in t.rows[0].cells]
            rows = []
            for row in t.rows[1:]:
                rows.append([cell.text.strip() for cell in row.cells])
            
            md_table = "| " + " | ".join(headers) + " |\n"
            md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            for r in rows:
                md_table += "| " + " | ".join(r) + " |\n"
                
            tables.append(ExtractedTable(
                headers=headers,
                rows=rows,
                markdown_representation=md_table.strip()
            ))
            
        full_text = "\n\n".join(text_lines)
        return [DocumentPage(
            page_number=1,
            text_content=full_text,
            tables=tables,
            raw_size_bytes=len(full_text.encode("utf-8"))
        )]

    @staticmethod
    def parse_pptx(filepath: Path) -> List[DocumentPage]:
        prs = Presentation(str(filepath))
        pages = []
        
        for idx, slide in enumerate(prs.slides, start=1):
            slide_texts = []
            if slide.shapes.title:
                slide_texts.append(f"# {slide.shapes.title.text.strip()}")
                
            for shape in slide.shapes:
                if shape == slide.shapes.title:
                    continue
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            slide_texts.append(text)
                            
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    slide_texts.append(f"\n> Speaker Notes: {notes}")
                    
            content = "\n\n".join(slide_texts)
            pages.append(DocumentPage(
                page_number=idx,
                text_content=content,
                raw_size_bytes=len(content.encode("utf-8"))
            ))
        return pages
```

**Step 2: Write Local Parser Unit Test**
Create `D:\TK\tests/test_local_parsers.py` using simple python-docx generation to test parsing:
```python
import pytest
from pathlib import Path
import docx
from contextforge.adapters.local_parsers import LocalDocumentParser

def test_docx_parser_integration(tmp_path):
    doc_path = tmp_path / "sample.docx"
    doc = docx.Document()
    doc.add_heading("Section Title", level=1)
    doc.add_paragraph("ContextForge core normalization pipeline validation.")
    doc.save(str(doc_path))
    
    pages = LocalDocumentParser.parse_docx(doc_path)
    assert len(pages) == 1
    assert "ContextForge" in pages[0].text_content
```

**Step 3: Run Tests**
Run: `pytest tests/test_local_parsers.py -v`
Expected: PASS

**Step 4: Commit**
```bash
git add contextforge/adapters/local_parsers.py tests/test_local_parsers.py
git commit -m "feat: implement local document parser adapters for PDF, DOCX, and PPTX"
```

---

### Task 4: AI Multimodal Ingestion Service
For high-fidelity structure extraction, diagrams, layout grids, or scanned documents, we'll implement an asynchronous service utilizing the Google GenAI client to parse pages layout-sensitively.

**Files:**
- Create: `D:\TK\contextforge/adapters/ai_parser.py`
- Create: `D:\TK\tests/test_ai_parser.py`

**Step 1: Write Async AI Vision Parser**
Create `D:\TK\contextforge/adapters/ai_parser.py`:
```python
import os
import asyncio
from pathlib import Path
from google import genai
from contextforge.core.models import DocumentPage

class AIPageParser:
    """Ingests documents page-by-page using multimodal Gemini AI models."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be configured in environment or .env file.")
        self.client = genai.Client(api_key=self.api_key)

    async def parse_document_async(self, filepath: Path) -> str:
        """Asynchronously uploads and processes document via Gemini 2.5 Flash."""
        # Use run_in_executor to avoid blocking the FastAPI main event loop during upload
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._parse, filepath)

    def _parse(self, filepath: Path) -> str:
        # Perform visual OCR and structure parsing
        uploaded_file = self.client.files.upload(file=filepath)
        
        prompt = """
        Normalize the attached document into token-efficient GFM Markdown.
        1. Preserving all tables as pure Markdown tables.
        2. Converting charts or layouts into clean Mermaid code blocks.
        3. Standardizing math formulas into clean LaTeX.
        4. Removing repetitive headers and footers.
        Output ONLY the clean Markdown text.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[uploaded_file, prompt]
            )
            return response.text
        finally:
            try:
                self.client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
```

**Step 2: Write Mock Tests for AI Ingest Service**
Create `D:\TK\tests/test_ai_parser.py`:
```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextforge.adapters.ai_parser import AIPageParser

@pytest.mark.asyncio
@patch("contextforge.adapters.ai_parser.genai.Client")
async def test_ai_parser_async(mock_client_class, tmp_path):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_file = MagicMock()
    mock_file.name = "files/test-doc"
    mock_client.files.upload.return_value = mock_file
    
    mock_response = MagicMock()
    mock_response.text = "# Normalized Markdown Output"
    mock_client.models.generate_content.return_value = mock_response
    
    parser = AIPageParser(api_key="mock-key")
    test_file = tmp_path / "mock.pdf"
    test_file.write_text("dummy")
    
    result = await parser.parse_document_async(test_file)
    assert "# Normalized Markdown Output" in result
```

**Step 3: Run Tests**
Run: `pytest tests/test_ai_parser.py -v`
Expected: PASS

**Step 4: Commit**
```bash
git add contextforge/adapters/ai_parser.py tests/test_ai_parser.py
git commit -m "feat: implement high-fidelity async AI multimodal parser powered by Gemini"
```

---

## Part 3: Semantic Optimization & Token Compression Engine

### Task 5: Intelligent Token Compression Service
Build a high-performance compression system that removes redundant phrasing, deduplicates headers, and condenses token footprints while preserving semantic value.

**Files:**
- Create: `D:\TK\contextforge/services/compression.py`
- Create: `D:\TK\tests/test_compression.py`

**Step 1: Write Token Compressor Service**
Create `D:\TK\contextforge/services/compression.py`:
```python
import re
from typing import List
from contextforge.analytics import count_tokens # importing our previous helper

class TokenCompressor:
    """Compresses GFM Markdown to maximize token efficiency."""
    
    @staticmethod
    def strip_metadata_bloat(text: str) -> str:
        """Removes duplicate lines, page header/footer templates, and redundant empty lines."""
        lines = text.split("\n")
        seen_lines = set()
        clean_lines = []
        
        # Simple header/footer regex pattern (e.g. Page 1 of 10, Confidentially notice, standard copyrights)
        suppress_pattern = re.compile(
            r"(page\s+\d+|confidential|copyright|all rights reserved|\d{1,2}/\d{1,2}/\d{2,4})", 
            re.IGNORECASE
        )
        
        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                clean_lines.append("")
                continue
                
            # Drop matching boilerplate lines
            if suppress_pattern.search(line_strip):
                continue
                
            # De-duplicate contiguous identical paragraphs/headings (OCR artifacts)
            if line_strip in seen_lines and len(line_strip) > 40:
                continue
                
            seen_lines.add(line_strip)
            clean_lines.append(line)
            
        # Join lines and deduplicate multi-newlines
        joined = "\n".join(clean_lines)
        return re.sub(r"\n{3,}", "\n\n", joined).strip()

    @staticmethod
    def compress_syntax(markdown_text: str) -> str:
        """Converts overly verbose list spaces, redundant margins, and layout artifacts into compact GFM syntax."""
        # Remove extra whitespace inside paragraphs while preserving linebreaks and double spaces
        compressed = re.sub(r"[ \t]+", " ", markdown_text)
        return compressed.strip()
```

**Step 2: Write Token Compression Unit Test**
Create `D:\TK\tests/test_compression.py`:
```python
from contextforge.services.compression import TokenCompressor

def test_boilerplate_stripping():
    bloated = (
        "## Title Section\n"
        "Page 1 of 2\n"
        "This is highly valuable text content.\n"
        "CONFIDENTIAL AND COPYRIGHT ALL RIGHTS RESERVED\n"
        "This is highly valuable text content." # duplicate sentence to ignore
    )
    clean = TokenCompressor.strip_metadata_bloat(bloated)
    assert "Page 1 of 2" not in clean
    assert "CONFIDENTIAL" not in clean
    assert "Title Section" in clean

def test_syntax_spacing_compression():
    raw_markdown = "Text     with   excessive    tabbed    spaces."
    compressed = TokenCompressor.compress_syntax(raw_markdown)
    assert compressed == "Text with excessive tabbed spaces."
```

**Step 3: Run Tests**
Run: `pytest tests/test_compression.py -v`
Expected: PASS

**Step 4: Commit**
```bash
git add contextforge/services/compression.py tests/test_compression.py
git commit -m "feat: implement token compression engine for semantic pruning and de-bloating"
```

---

### Task 6: Semantic Chunker & Knowledge Graph Extraction Service
Generate highly structured output by chunking the normalized Markdown semantically (rather than randomly splitting by word count) and extracting core entities.

**Files:**
- Create: `D:\TK\contextforge/services/chunking.py`
- Create: `D:\TK\tests/test_chunking.py`

**Step 1: Write Semantic Chunker & Entity Service**
Create `D:\TK\contextforge/services/chunking.py`:
```python
import re
from typing import List, Dict
from contextforge.core.models import ExtractedEntity

class SemanticChunker:
    """Splits Markdown based on heading structures and semantic content blocks."""
    
    @staticmethod
    def chunk_markdown(text: str, max_chunk_tokens: int = 400) -> List[str]:
        # Split primarily on heading boundary transitions (#, ##, ###)
        sections = re.split(r"(^#+\s+.*$)", text, flags=re.MULTILINE)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for section in sections:
            section_strip = section.strip()
            if not section_strip:
                continue
                
            # Estimate word token size
            words = section_strip.split()
            word_count = len(words)
            
            if current_length + word_count > max_chunk_tokens and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [section_strip]
                current_length = word_count
            else:
                current_chunk.append(section_strip)
                current_length += word_count
                
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
            
        return chunks

class EntityExtractor:
    """Rule-based core entity extractor for quick semantic tagging."""
    
    @staticmethod
    def extract_entities(text: str) -> List[ExtractedEntity]:
        entities = []
        
        # Simple extraction heuristics (Capitalized names, specific indicators)
        org_pattern = re.compile(r"([A-Z][a-zA-Z0-9&]+(?:\s+[A-Z][a-zA-Z0-9]+)*\s+(?:Corp|Corporation|Inc|LLC|Ltd|University|Institute|Engine))")
        date_pattern = re.compile(r"(\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b)")
        
        for match in org_pattern.finditer(text):
            entities.append(ExtractedEntity(
                name=match.group(1),
                category="Organization",
                context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)].strip()
            ))
            
        for match in date_pattern.finditer(text):
            entities.append(ExtractedEntity(
                name=match.group(1),
                category="Date",
                context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)].strip()
            ))
            
        # De-duplicate entities by name
        unique_entities = {}
        for ent in entities:
            if ent.name not in unique_entities:
                unique_entities[ent.name] = ent
                
        return list(unique_entities.values())
```

**Step 2: Write Chunker Unit Test**
Create `D:\TK\tests/test_chunking.py`:
```python
from contextforge.services.chunking import SemanticChunker, EntityExtractor

def test_heading_aware_chunking():
    markdown = (
        "# Heading A\n"
        "Content paragraph describing point A.\n"
        "# Heading B\n"
        "Content paragraph describing point B."
    )
    chunks = SemanticChunker.chunk_markdown(markdown, max_chunk_tokens=5)
    assert len(chunks) >= 2
    assert "Heading A" in chunks[0]
    assert "Heading B" in chunks[1]

def test_heuristic_entity_extraction():
    text = "The team at Google Corp launched the service on 15 March 2026."
    entities = EntityExtractor.extract_entities(text)
    assert any(ent.name == "Google Corp" for ent in entities)
    assert any(ent.category == "Date" for ent in entities)
```

**Step 3: Run Tests**
Run: `pytest tests/test_chunking.py -v`
Expected: PASS

**Step 4: Commit**
```bash
git add contextforge/services/chunking.py tests/test_chunking.py
git commit -m "feat: implement semantic chunker and core entity extraction service"
```

---

## Part 4: Presentation & FastAPI Web Integration Layer

### Task 7: REST API Core Service & Entrypoint
Build a clean, robust, and asynchronous web API exposing normalization and context optimization services.

**Files:**
- Create: `D:\TK\contextforge/api/app.py`
- Create: `D:\TK\main.py`
- Create: `D:\TK\tests/test_api.py`

**Step 1: Write FastAPI Application**
Create the unified app definition in `D:\TK\contextforge/api/app.py`:
```python
import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextforge.core.models import AIContextPackage, TokenMetrics
from contextforge.adapters.local_parsers import LocalDocumentParser
from contextforge.adapters.ai_parser import AIPageParser
from contextforge.services.compression import TokenCompressor
from contextforge.services.chunking import SemanticChunker, EntityExtractor
from contextforge.analytics import count_tokens, compute_savings

app = FastAPI(
    title="ContextForge Core Optimization Service",
    description="Intelligent pre-computation normalization engine for massive context savings.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "ContextForge Core"}

@app.post("/normalize", response_model=AIContextPackage)
async def normalize_document(
    file: UploadFile = File(...),
    use_ai: bool = Form(default=False)
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {suffix}")
        
    # Write to a temporary file for parsing compatibility
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = Path(temp_file.name)
        
    try:
        # Step 1: Normalization Parser Selection
        if use_ai or suffix in [".png", ".jpg", ".jpeg", ".webp"]:
            parser = AIPageParser()
            markdown_raw = await parser.parse_document_async(temp_path)
        else:
            if suffix == ".pdf":
                pages = LocalDocumentParser.parse_pdf(temp_path)
            elif suffix == ".docx":
                pages = LocalDocumentParser.parse_docx(temp_path)
            elif suffix == ".pptx":
                pages = LocalDocumentParser.parse_pptx(temp_path)
            else:
                raise HTTPException(status_code=400, detail="Invalid path mapping")
            markdown_raw = "\n\n---\n\n".join([p.text_content for p in pages])
            
        # Step 2: Intelligent Token Compression
        clean_markdown = TokenCompressor.strip_metadata_bloat(markdown_raw)
        clean_markdown = TokenCompressor.compress_syntax(clean_markdown)
        
        # Step 3: Semantic Chunking & Entities
        chunks = SemanticChunker.chunk_markdown(clean_markdown)
        entities = EntityExtractor.extract_entities(clean_markdown)
        
        # Step 4: Token Analytics
        raw_token_proxy = len(content) // 2 # byte to token proxy
        metrics_dict = compute_savings(raw_token_proxy, clean_markdown)
        
        metrics = TokenMetrics(
            raw_tokens_estimate=metrics_dict["raw_tokens"],
            compressed_tokens=metrics_dict["markdown_tokens"],
            tokens_saved=metrics_dict["tokens_saved"],
            savings_percentage=metrics_dict["savings_percentage"]
        )
        
        return AIContextPackage(
            document_name=file.filename,
            metadata={"file_type": suffix, "use_ai_ocr": str(use_ai)},
            full_markdown=clean_markdown,
            entities=entities,
            chunks=chunks,
            metrics=metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context optimization execution failed: {str(e)}")
    finally:
        # Clean up local temporary file
        if temp_path.exists():
            os.unlink(temp_path)
```

Create base CLI entrypoint `D:\TK\main.py` referencing the web app:
```python
import uvicorn
import sys

def start_dev_server():
    print("Launching ContextForge FastAPI Server...")
    uvicorn.run("contextforge.api.app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        start_dev_server()
    else:
        print("Usage: python main.py web (runs the web engine)")
```

**Step 2: Write API Integration Test Suite**
Create `D:\TK\tests/test_api.py` to test server route resolution:
```python
import pytest
from fastapi.testclient import TestClient
from contextforge.api.app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_invalid_normalization_format():
    response = client.post(
        "/normalize",
        files={"file": ("test.exe", b"invalid-binary-content", "application/octet-stream")},
        data={"use_ai": "false"}
    )
    assert response.status_code == 400
```

**Step 3: Execute Test Suite**
Run: `pytest tests/test_api.py -v`
Expected: PASS

**Step 4: Commit**
```bash
git add contextforge/api/app.py main.py tests/test_api.py
git commit -m "feat: implement async REST API endpoints and integrate core pipeline flow"
```
