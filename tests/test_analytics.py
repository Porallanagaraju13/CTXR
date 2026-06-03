import pytest
from contextforge.analytics import count_tokens, compute_savings

def test_count_tokens_valid():
    text = "Hello, this is ContextForge! High performance normalization."
    tokens = count_tokens(text)
    assert tokens > 0

def test_count_tokens_empty():
    assert count_tokens("") == 0
    assert count_tokens(None) == 0

def test_count_tokens_multi_model():
    text = "Hello, this is ContextForge! High performance normalization." * 10
    gpt4_tokens = count_tokens(text, "gpt-4")
    gpt4o_tokens = count_tokens(text, "gpt-4o")
    claude_tokens = count_tokens(text, "claude-3-5-sonnet")
    gemini_tokens = count_tokens(text, "gemini-2.5-flash")
    
    assert gpt4_tokens > 0
    assert gpt4o_tokens > 0
    assert claude_tokens > 0
    assert gemini_tokens > 0
    
    # Assert scaling properties
    assert claude_tokens == int(gpt4_tokens * 1.05)
    assert gemini_tokens == int(gpt4_tokens * 1.08)

def test_compute_savings_standard():
    raw_text = "This is some bloated redundant text content from a PDF file that needs metadata removal." * 5
    compressed_text = "Clean normal text."
    
    stats = compute_savings(raw_text, compressed_text, "gpt-4")
    assert stats["raw_tokens"] > stats["markdown_tokens"]
    assert stats["tokens_saved"] > 0
    assert stats["savings_percentage"] > 0.0
    assert "dollars_saved" in stats
    assert stats["dollars_saved"] > 0.0

def test_compute_savings_empty_raw():
    stats = compute_savings("", "content")
    assert stats["raw_tokens"] == 0
    assert stats["savings_percentage"] == 0.0
    assert stats["dollars_saved"] == 0.0

def test_compute_savings_multi_model_pricing():
    raw_text = "Highly redundant context page information " * 20
    compressed_text = "Optimized page."
    
    stats_gpt4 = compute_savings(raw_text, compressed_text, "gpt-4")
    stats_gpt4o = compute_savings(raw_text, compressed_text, "gpt-4o")
    
    assert stats_gpt4["dollars_saved"] > stats_gpt4o["dollars_saved"]

