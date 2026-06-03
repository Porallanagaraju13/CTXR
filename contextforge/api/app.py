import os
import tempfile
import logging
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextforge.core.models import AIContextPackage, TokenMetrics, PromptOptimizationResult
from contextforge.adapters.local_parsers import LocalDocumentParser
from contextforge.adapters.ai_parser import AIPageParser
from contextforge.services.compression import TokenCompressor
from contextforge.services.chunking import SemanticChunker, EntityExtractor
from contextforge.services.prompt_optimizer import PromptOptimizer
from contextforge.analytics import compute_savings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContextForge")

app = FastAPI(
    title="ContextForge Core Optimization Engine",
    description="Intelligent pre-computation normalization engine for massive context savings.",
    version="1.0.0"
)

# Enable CORS for Chrome extension and web frontend integration
# Wildcard is required because Chrome extensions use chrome-extension:// origins
# which cannot be enumerated ahead of time (extension ID changes per install)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_FORMATS = [".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".webp"]

# ── Keep-Alive Self-Ping (prevents Render free tier cold starts) ─────────
KEEP_ALIVE_INTERVAL = 13 * 60  # 13 minutes (Render sleeps after 15 min)
RENDER_SERVICE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://contextforge-kub5.onrender.com")

async def _keep_alive_pinger():
    """Background task that pings /health every 13 minutes to prevent Render sleep."""
    import httpx
    await asyncio.sleep(60)  # Wait 1 min after startup before first ping
    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{RENDER_SERVICE_URL}/health")
                logger.info(f"[Keep-Alive] Pinged /health → {resp.status_code}")
        except Exception as e:
            logger.warning(f"[Keep-Alive] Ping failed: {e}")
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)

@app.on_event("startup")
async def start_keep_alive():
    """Launch keep-alive pinger only in production (on Render)."""
    if os.getenv("ENVIRONMENT") == "production":
        asyncio.create_task(_keep_alive_pinger())
        logger.info(f"[Keep-Alive] Background pinger started (every {KEEP_ALIVE_INTERVAL}s)")

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Standard service health check endpoint.
    """
    return {
        "status": "healthy",
        "engine": "ContextForge Core",
        "supported_formats": SUPPORTED_FORMATS
    }

@app.post("/normalize", response_model=AIContextPackage, status_code=status.HTTP_200_OK)
async def normalize_document(
    file: UploadFile = File(...),
    use_ai: bool = Form(default=False),
    chunk_size: int = Form(default=350, description="Max word count per semantic chunk"),
    target_model: str = Form(default="gpt-4", description="Target model for tokenizer calculations (e.g. gpt-4, gpt-4o, claude, gemini)"),
    extract_entities: bool = Form(default=True, description="Enable key entity classification metadata tagging"),
    deduplicate_boilerplate: bool = Form(default=True, description="Enable dynamic inter-page headers/footers deduplication")
):
    """
    Core normalization endpoint.
    Accepts heterogeneous documents, runs them through the optimization engine,
    and returns a structured, token-compressed AI Context Package with configurable parameters.
    """
    logger.info(f"Received normalization request: file={file.filename}, use_ai={use_ai}, model={target_model}")
    
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        logger.warning(f"Unsupported file format rejected: {suffix}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: '{suffix}'. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Securely write uploaded stream to a local temporary file
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty."
                )
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        # Step 1: Normalization & Parsing Selection
        if use_ai or suffix in [".png", ".jpg", ".jpeg", ".webp"]:
            # Leverage Gemini Vision API for visual structures, OCR correcting and scans
            logger.info("Routing file to AI-Vision extraction pipeline...")
            try:
                ai_parser = AIPageParser()
                markdown_raw = await ai_parser.parse_document_async(temp_path)
            except ValueError as val_err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(val_err)
                )
        else:
            # Leverage high-performance, cost-free local parsing engines
            logger.info("Routing file to Local parsing engine...")
            if suffix == ".pdf":
                pages = LocalDocumentParser.parse_pdf(temp_path)
            elif suffix == ".docx":
                pages = LocalDocumentParser.parse_docx(temp_path)
            elif suffix == ".pptx":
                pages = LocalDocumentParser.parse_pptx(temp_path)
            else:
                raise HTTPException(status_code=500, detail="Adapter routing error.")
            
            markdown_raw = "\n\n---\n\n".join([p.text_content for p in pages])

        # Step 2: Intelligent Token Compression
        logger.info("Compressing document syntax and stripping metadata bloat...")
        if deduplicate_boilerplate:
            clean_markdown = TokenCompressor.strip_metadata_bloat(markdown_raw)
        else:
            clean_markdown = markdown_raw
            
        clean_markdown = TokenCompressor.compress_syntax(clean_markdown)

        # Step 3: Semantic Chunking & Entity Extraction
        logger.info("Segmenting context semantically and indexing entities...")
        chunks = SemanticChunker.chunk_markdown(clean_markdown, max_chunk_words=chunk_size)
        
        entities = []
        if extract_entities:
            entities = EntityExtractor.extract_entities(clean_markdown)

        # Step 4: Calculate Token footprint reductions
        # Proxy raw tokens from size bytes vs compressed markdown tokens
        raw_token_proxy = len(content) // 2
        metrics_dict = compute_savings(raw_token_proxy, clean_markdown, model_name=target_model)

        metrics = TokenMetrics(
            raw_tokens_estimate=metrics_dict["raw_tokens"],
            compressed_tokens=metrics_dict["markdown_tokens"],
            tokens_saved=metrics_dict["tokens_saved"],
            savings_percentage=metrics_dict["savings_percentage"],
            dollars_saved=metrics_dict["dollars_saved"]
        )

        logger.info(f"Normalization complete. Token Footprint reduced by {metrics.savings_percentage}%!")

        return AIContextPackage(
            document_name=file.filename,
            metadata={"file_type": suffix, "use_ai_ocr": str(use_ai), "target_model": target_model},
            full_markdown=clean_markdown,
            entities=entities,
            chunks=chunks,
            metrics=metrics
        )

    except HTTPException as http_ex:
        # Re-raise explicit HTTP exceptions
        raise http_ex
    except Exception as e:
        logger.error(f"ContextForge pipeline execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context optimization pipeline execution failed: {str(e)}"
        )
    finally:
        # Guarantee local temp file cleanup
        if temp_path and temp_path.exists():
            try:
                os.unlink(temp_path)
                logger.info("Temporary ingestion files cleaned up successfully.")
            except Exception as cleanup_err:
                logger.error(f"Failed to delete temp file {temp_path}: {cleanup_err}")


@app.post("/optimize-prompt", response_model=PromptOptimizationResult, status_code=status.HTTP_200_OK)
async def optimize_prompt(
    prompt: str = Form(..., description="Raw user prompt text to optimize"),
    use_ai: bool = Form(default=False, description="Enable AI-powered rewriting via Gemini for deeper compression"),
    target_model: str = Form(default="gpt-4", description="Target model for tokenizer calculations (e.g. gpt-4, gpt-4o, claude, gemini)")
):
    """
    Prompt Optimization Endpoint.
    Accepts raw user prompts, applies rule-based compression and optional AI rewriting,
    then returns the optimized prompt with token savings metrics.
    """
    logger.info(f"Received prompt optimization request: length={len(prompt)}, use_ai={use_ai}, model={target_model}")

    if not prompt or not prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt text cannot be empty."
        )

    try:
        original_prompt = prompt

        # Stage 1: Rule-based optimization (always runs first)
        logger.info("Running rule-based prompt compression pipeline...")
        optimized_text, techniques = PromptOptimizer.optimize(prompt)

        # Stage 2: Optional AI-powered rewriting for deeper compression
        if use_ai:
            logger.info("Routing to AI-powered prompt rewriting...")
            try:
                ai_parser = AIPageParser()
                ai_rewritten = await ai_parser.rewrite_prompt_async(optimized_text)
                if ai_rewritten and len(ai_rewritten.strip()) > 0:
                    optimized_text = ai_rewritten
                    techniques.append("AI-powered semantic rewriting (Gemini)")
            except ValueError as val_err:
                logger.warning(f"AI rewriting unavailable, using rule-based result: {val_err}")
            except Exception as ai_err:
                logger.warning(f"AI rewriting failed, falling back to rule-based result: {ai_err}")

        # Stage 3: Calculate token savings metrics
        metrics_dict = compute_savings(original_prompt, optimized_text, model_name=target_model)
        metrics = TokenMetrics(
            raw_tokens_estimate=metrics_dict["raw_tokens"],
            compressed_tokens=metrics_dict["markdown_tokens"],
            tokens_saved=metrics_dict["tokens_saved"],
            savings_percentage=metrics_dict["savings_percentage"],
            dollars_saved=metrics_dict["dollars_saved"]
        )

        logger.info(f"Prompt optimization complete. Reduction: {metrics.savings_percentage}% ({metrics.tokens_saved} tokens saved)")

        return PromptOptimizationResult(
            original_prompt=original_prompt,
            optimized_prompt=optimized_text,
            optimization_techniques=techniques,
            metrics=metrics
        )

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Prompt optimization pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prompt optimization failed: {str(e)}"
        )
