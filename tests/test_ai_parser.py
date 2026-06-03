import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextforge.adapters.ai_parser import AIPageParser

@pytest.mark.asyncio
@patch("contextforge.adapters.ai_parser.genai.Client")
async def test_ai_parser_mocked_flow(mock_client_class, tmp_path):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock upload file response
    mock_file = MagicMock()
    mock_file.name = "files/test-gemini-file"
    mock_client.files.upload.return_value = mock_file
    
    # Mock model generation response
    mock_response = MagicMock()
    mock_response.text = "# Normalized Core Context Package\n\n- Entity: ContextForge"
    mock_client.models.generate_content.return_value = mock_response
    
    parser = AIPageParser(api_key="mocked-api-key")
    dummy_file = tmp_path / "sample.pdf"
    dummy_file.write_text("fake pdf data")
    
    markdown_result = await parser.parse_document_async(dummy_file)
    assert "# Normalized Core Context Package" in markdown_result
    assert "- Entity: ContextForge" in markdown_result
    
    # Assert network upload and deletes were made
    mock_client.files.upload.assert_called_once()
    mock_client.files.delete.assert_called_once_with(name="files/test-gemini-file")
dummy_file = None
