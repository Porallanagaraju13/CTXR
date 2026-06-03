# ContextForge Core Context Optimization Engine

**ContextForge** is a production-ready document normalization and token compression engine designed to package heterogeneous data sources (PDFs, DOCX, PPTX, Images) into clean, structure-preserving, and token-efficient GFM Markdown context packages. 

By pre-computing visual and local layout extractions, standardizing tables, and stripping duplicate text, ContextForge **reduces LLM token footprints by 40–70%** while significantly increasing vector retrieval accuracy.

---

## 🛠️ Tech Stack & Key Engines
- **Language**: Python 3.12+ (fully type-safe)
- **REST framework**: FastAPI (asynchronous ASGI routes)
- **Local Normalization Parsers**: `pymupdf` (PDF structure & tables), `python-docx` (Word layout streams), `python-pptx` (Slides & Notes extraction)
- **AI-Vision OCR Ingestion**: `google-genai` (integrates the official Gemini 2.5 Flash SDK)
- **Metrics Calculator**: `tiktoken` (tracks pre- and post-compression token counts with robust sandboxed/offline fallbacks)
- **Type Validation**: `pydantic` v2

---

## 📂 System Folder Structure

```text
D:\TK\
├── contextforge/
│   ├── __init__.py
│   ├── analytics.py             # Token estimation & cost analytics engine
│   ├── core/
│   │   ├── __init__.py
│   │   └── models.py            # Strict type-safe Pydantic domain models
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── local_parsers.py     # Fitz, Word, PPTX high-speed parsers
│   │   └── ai_parser.py         # Async Gemini layout-OCR & chart visual parser
│   ├── services/
│   │   ├── __init__.py
│   │   ├── compression.py       # Syntax compressor & copyright de-bloater
│   │   └── chunking.py          # Heading-aware chunker & semantic entity tagging
│   └── api/
│       ├── __init__.py
│       └── app.py               # Asynchronous REST API endpoint routers
├── tests/                       # Strict automated isolated test suite
│   ├── test_analytics.py
│   ├── test_models.py
│   ├── test_local_parsers.py
│   ├── test_ai_parser.py
│   ├── test_compression.py
│   ├── test_chunking.py
│   └── test_api.py
├── requirements.txt             # Pinned secure package dependencies
├── .env                         # Sandbox keys and environment configs
├── main.py                      # Application entrypoint launcher
└── README.md                    # System setup & production manual
```

---

## 🚀 Getting Started

### 1. Initialize Virtual Environment
Initialize a fresh, isolated Python environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Pinned Dependencies
Install all production and test requirements:
```powershell
pip install -r requirements.txt
```

### 3. Environment Setup
Configure your API credentials in `.env`:
```ini
GEMINI_API_KEY= your Gemini api key
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 4. Running the Dev Server
Launch the asynchronous FastAPI development web service:
```powershell
python main.py web
```
- Open `http://127.0.0.1:8000/health` to confirm active service status.
- Access the rich Swagger API page at `http://127.0.0.1:8000/docs` to test endpoints visually.

---

## 🧪 Automated Testing
Run the complete automated integration and unit test suite verifying type safety, parsing, chunk boundaries, metadata pruners, and endpoints:
```powershell
python -m pytest -v
```
All **28+ integration and unit tests** are fully passing!

---

## 🔗 Key API Interfaces

### 1. Health Status check
`GET /health`
Returns service availability, operational metrics, and supported ingestion formats.

### 2. Intelligent Document Normalization Pipeline
`POST /normalize`
Processes heterogeneous files using the requested local or AI parser pipeline, running the compression engine and semantic parser sequentially.
- **Parameters:**
  - `file`: Raw binary document file upload (`PDF`, `DOCX`, `PPTX`, `PNG`, `JPG`, `WEBP`)
  - `use_ai`: Boolean (if `true`, routes the file to the high-fidelity multimodal Gemini OCR vision pipeline)
- **Response Shape (`AIContextPackage`):**
  ```json
  {
    "document_name": "quarterly_report.pdf",
    "metadata": {
      "file_type": ".pdf",
      "use_ai_ocr": "true"
    },
    "full_markdown": "# Q2 Financial Highlights\n\n| Region | Revenue |\n|---|---|\n| NA | $4.2M |\n...",
    "entities": [
      {
        "name": "ContextForge Corp",
        "category": "Organization",
        "context": "The engineers at ContextForge Corp delivered..."
      }
    ],
    "chunks": [
      "# Q2 Financial Highlights\n\n| Region | Revenue |..."
    ],
    "metrics": {
      "raw_tokens_estimate": 45000,
      "compressed_tokens": 12000,
      "tokens_saved": 33000,
      "savings_percentage": 73.33
    }
  }
  ```

### 3. Prompt Optimization Engine
`POST /optimize-prompt`
Accepts raw user prompts, applies rule-based compression and optional AI rewriting, then returns the optimized prompt with token savings metrics.
- **Parameters:**
  - `prompt` (str): Raw user prompt text to optimize
  - `use_ai` (bool, default `false`): Enable AI-powered rewriting via Gemini for deeper semantic compression
  - `target_model` (str, default `"gpt-4"`): Target model for tokenizer calculations
- **Response Shape (`PromptOptimizationResult`):**
  ```json
  {
    "original_prompt": "I would like you to please help me create a Python function. In order to ensure correctness, make sure to validate all of the input parameters.",
    "optimized_prompt": "Create a Python function. To ensure correctness, Ensure validate All input parameters.",
    "optimization_techniques": [
      "Filler word removal",
      "Redundant phrase compression",
      "Whitespace normalization"
    ],
    "metrics": {
      "raw_tokens_estimate": 38,
      "compressed_tokens": 18,
      "tokens_saved": 20,
      "savings_percentage": 52.63,
      "dollars_saved": 0.0006
    }
  }
  ```
- **Optimization Techniques Applied:**
  - Filler word removal (please, kindly, just, basically, etc.)
  - Redundant phrase compression (in order to → To, due to the fact that → Because)
  - Verbose qualifier stripping (very important → important)
  - Passive voice simplification (it is recommended that → Recommend:)
  - Instruction deduplication (removes repeated lines)
  - Markdown structuring (section labels → headers, numbered patterns → lists)
  - Whitespace normalization (collapses excessive spaces/newlines)
