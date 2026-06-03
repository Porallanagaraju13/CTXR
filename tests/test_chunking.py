import pytest
from contextforge.services.chunking import SemanticChunker, EntityExtractor

def test_heading_aware_chunk_boundaries():
    markdown = (
        "# Part 1: Background\n"
        "This describes the core business background.\n\n"
        "## Part 2: Implementation\n"
        "We implementation Next.js, FastAPI, and Qdrant in this codebase."
    )
    chunks = SemanticChunker.chunk_markdown(markdown, max_chunk_words=10)
    assert len(chunks) >= 2
    assert "Part 1" in chunks[0]
    assert "Part 2" in chunks[1]
    # Verify hierarchical breadcrumbs context prefixes
    assert "# [Context: Part 1: Background]" in chunks[0]
    assert "# [Context: Part 1: Background > Part 2: Implementation]" in chunks[1]

def test_entity_extraction_technology_and_orgs():
    text = (
        "The engineer at ContextForge Corp launched FastAPI services in London on 12 June 2026. "
        "You can contact support at contact@contextforge.ai or +1-555-019-2834. "
        "This project saved the client $4.2M and 15000 USD."
    )
    entities = EntityExtractor.extract_entities(text)
    
    assert any(e.name == "ContextForge Corp" and e.category == "Organization" for e in entities)
    assert any(e.name == "FastAPI" and e.category == "Technology" for e in entities)
    # Check normalized date
    assert any(e.name == "2026-06-12" and e.category == "Date" for e in entities)
    # Check new entity types
    assert any(e.name == "London" and e.category == "Location" for e in entities)
    assert any(e.name == "contact@contextforge.ai" and e.category == "Email" for e in entities)
    assert any(e.name == "+1-555-019-2834" and e.category == "Phone" for e in entities)
    assert any(e.name == "$4.2M" and e.category == "Monetary" for e in entities)
    assert any(e.name == "15000 USD" and e.category == "Monetary" for e in entities)
