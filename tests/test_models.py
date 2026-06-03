import pytest
from pydantic import ValidationError
from contextforge.core.models import ExtractedTable, ExtractedEntity, TokenMetrics, AIContextPackage

def test_extracted_table_validation():
    table = ExtractedTable(
        headers=["A", "B"],
        rows=[["1", "2"]],
        markdown_representation="| A | B |\n|---|---|\n| 1 | 2 |"
    )
    assert table.headers == ["A", "B"]
    assert table.rows == [["1", "2"]]

def test_extracted_entity_validation():
    entity = ExtractedEntity(
        name="FastAPI",
        category="Technology",
        context="We use FastAPI for routes."
    )
    assert entity.name == "FastAPI"
    assert entity.category == "Technology"

def test_token_metrics_validation():
    metrics = TokenMetrics(
        raw_tokens_estimate=1000,
        compressed_tokens=300,
        tokens_saved=700,
        savings_percentage=70.0,
        dollars_saved=0.021
    )
    assert metrics.tokens_saved == 700
    assert metrics.savings_percentage == 70.0
    assert metrics.dollars_saved == 0.021
