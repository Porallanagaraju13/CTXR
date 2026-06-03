import os
import asyncio
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types

class AIPageParser:
    """
    Ingests and parses documents/images page-by-page using Google's Multimodal Gemini APIs.
    Preserves tables, visual assets, math equations, and flow charts as clean GFM Markdown/Mermaid.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY must be configured. Please set it in your environment or .env file."
            )
        # Use the official google-genai client
        self.client = genai.Client(api_key=self.api_key)

    async def parse_document_async(self, filepath: Path) -> str:
        """
        Asynchronously processes a document page/image via the Gemini 2.5 Flash model.
        Runs blocking network I/O operations inside an executor thread.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Input file not found at: {filepath}")
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._parse, filepath)

    def _parse(self, filepath: Path) -> str:
        """
        Synchronous helper executed inside the thread pool executor.
        Handles remote upload, multimodal generation, and cleanup.
        """
        print(f"[ContextForge AI] Uploading {filepath.name} to Gemini OCR engine...")
        uploaded_file = self.client.files.upload(file=filepath)
        
        prompt = """
        You are an elite Document Normalizer. Your job is to convert the attached document into clean, token-efficient, structure-preserving Markdown.
        
        Follow these strict parsing rules:
        1. Maintain headings structure (# for Document Title, ## for Pages/Slides, ### for Section Headings).
        2. Convert all tables into clean, valid GitHub Flavored Markdown (GFM) tables.
        3. Convert any visual flowcharts or diagrams into beautiful syntax-valid Mermaid.js blocks.
        4. Transcribe mathematical formulas into clean inline LaTeX ($...$) or block LaTeX ($$...$$).
        5. Omit repetitive headers, page footers, and page numbers to save tokens.
        6. Do NOT include your own conversational text, explanations, or wrappers. Output ONLY the raw Markdown representation of the document.
        """
        
        try:
            print("[ContextForge AI] Performing visual layout-aware generation...")
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[uploaded_file, prompt]
            )
            return response.text
        finally:
            # Always delete the uploaded file from Google's temporary servers
            try:
                print(f"[ContextForge AI] Cleaning up temporary file {uploaded_file.name} from Google servers...")
                self.client.files.delete(name=uploaded_file.name)
            except Exception as e:
                print(f"[ContextForge AI] Warning: Failed to clean up file from remote: {e}")

    async def rewrite_prompt_async(self, prompt_text: str) -> str:
        """
        Uses Gemini to intelligently rewrite and compress a user prompt
        while preserving all semantic meaning and intent.
        """
        if not prompt_text or not prompt_text.strip():
            return prompt_text

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._rewrite_prompt, prompt_text)

    def _rewrite_prompt(self, prompt_text: str) -> str:
        """
        Synchronous helper for AI-powered prompt rewriting.
        Uses gemini-2.0-flash for low-latency compression.
        """
        rewrite_instruction = """Compress this prompt: keep ALL meaning, constraints, and data. Output ONLY the rewritten prompt.
Rules: use GFM markdown (headers, bullets, code fences), imperative voice, no filler words, no explanations.

Prompt:
"""
        print("[CTXR AI] Performing AI-powered prompt rewriting...")
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[rewrite_instruction + prompt_text]
        )
        return response.text.strip()

