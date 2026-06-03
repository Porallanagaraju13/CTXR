import pytest
from contextforge.services.compression import TokenCompressor

def test_boilerplate_copyright_removal():
    raw_text = (
        "ContextForge documentation\n"
        "Page 4 of 20\n"
        "Copyright © 2026 ContextForge Corp. All rights reserved.\n"
        "This is highly valuable text."
    )
    clean = TokenCompressor.strip_metadata_bloat(raw_text)
    assert "Page 4" not in clean
    assert "Copyright" not in clean
    assert "valuable text" in clean

def test_duplicate_ocr_lines_removal():
    raw_text = (
        "This is an exceptionally long paragraph that got duplicated twice due to visual OCR overlap errors.\n"
        "This is an exceptionally long paragraph that got duplicated twice due to visual OCR overlap errors."
    )
    clean = TokenCompressor.strip_metadata_bloat(raw_text)
    # The duplicate should be stripped since it's identical and long
    lines = [l for l in clean.split("\n") if l.strip()]
    assert len(lines) == 1

def test_syntax_horizontal_spaces_compression():
    raw_text = "#  Heading  Spacing \n\nBody   text    with    excessive   spacing."
    clean = TokenCompressor.compress_syntax(raw_text)
    assert clean == "# Heading Spacing\n\nBody text with excessive spacing."

def test_dynamic_header_footer_pruning():
    # Construct a multi-page document with a recurring custom book title at the top
    # and a custom confidentiality label at the bottom of pages.
    raw_pages = [
        "Internal Project Report v1.2\n## Introduction\nSome content for page 1.\nCONFIDENTIALITY NOTICE",
        "Internal Project Report v1.2\n## Methodology\nSome content for page 2.\nCONFIDENTIALITY NOTICE",
        "Internal Project Report v1.2\n## Results\nSome content for page 3.\nCONFIDENTIALITY NOTICE",
    ]
    raw_text = "\n\n---\n\n".join(raw_pages)
    
    clean = TokenCompressor.strip_metadata_bloat(raw_text)
    
    assert "Internal Project Report" not in clean
    assert "CONFIDENTIALITY NOTICE" not in clean
    assert "Introduction" in clean
    assert "Methodology" in clean
    assert "Results" in clean
