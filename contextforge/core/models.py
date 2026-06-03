from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ExtractedTable(BaseModel):
    headers: List[str] = Field(default_factory=list, description="Headers of the extracted table")
    rows: List[List[str]] = Field(default_factory=list, description="Rows of the extracted table")
    markdown_representation: str = Field(..., description="GFM markdown representation of the table")

class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Name of the semantic entity")
    category: str = Field(..., description="Semantic class (e.g. Person, Org, Date, Technology)")
    context: str = Field(..., description="Local snippet surrounding the entity context")

class DocumentPage(BaseModel):
    page_number: int = Field(..., description="Sequential page number of the original document")
    text_content: str = Field(..., description="Extracted raw or OCR-processed text")
    headings: List[str] = Field(default_factory=list, description="Extracted headings on this page")
    tables: List[ExtractedTable] = Field(default_factory=list, description="Tables discovered on this page")
    raw_size_bytes: int = Field(..., description="Total size in bytes of raw data extracted")

class TokenMetrics(BaseModel):
    raw_tokens_estimate: int = Field(..., description="Estimated size of original raw document in tokens")
    compressed_tokens: int = Field(..., description="Token size of pre-computed Markdown context package")
    tokens_saved: int = Field(..., description="Count of LLM tokens saved")
    savings_percentage: float = Field(..., description="Context footprint cost reduction percentage")
    dollars_saved: float = Field(default=0.0, description="Approximate financial cost savings in dollars")

class AIContextPackage(BaseModel):
    document_name: str = Field(..., description="Original name of the uploaded document")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Metadata dictionary (file type, tags)")
    full_markdown: str = Field(..., description="Normalized, compressed GFM Markdown string")
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted key entities")
    chunks: List[str] = Field(default_factory=list, description="Semantic chunks of normalized content")
    metrics: TokenMetrics = Field(..., description="Detailed token optimization metrics scorecard")

class PromptOptimizationResult(BaseModel):
    original_prompt: str = Field(..., description="The original unmodified user prompt")
    optimized_prompt: str = Field(..., description="The compressed, token-efficient markdown prompt")
    optimization_techniques: List[str] = Field(default_factory=list, description="List of optimization techniques applied")
    metrics: TokenMetrics = Field(..., description="Token savings metrics scorecard")
