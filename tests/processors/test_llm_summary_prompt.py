import pytest
import unittest.mock
from unittest.mock import MagicMock
from marker.processors.llm.llm_summary import LLMSummaryProcessor
from marker.schema import BlockTypes
from marker.schema.blocks.figure import Figure
from marker.schema.blocks.picture import Picture
from marker.schema.blocks.base import Block
from marker.schema.polygon import PolygonBox

@pytest.fixture
def mock_document():
    doc = MagicMock()
    return doc

@pytest.fixture
def processor():
    return LLMSummaryProcessor()

def test_llm_summary_processor_block_types(processor):
    assert BlockTypes.Figure in processor.block_types
    assert BlockTypes.Picture in processor.block_types

def test_llm_summary_processor_context_from_description(processor, mock_document):
    # Test Figure with description
    figure = Figure(
        polygon=PolygonBox.from_bbox([0, 0, 100, 100]),
        page_id=0,
        block_id=0,
        description="A test chart description"
    )
    # Mock raw_text to return empty string for figure
    with unittest.mock.patch.object(Figure, 'raw_text', return_value=""):
        mock_document.pages = [MagicMock()]
        mock_document.pages[0].contained_blocks.return_value = [figure]
        
        prompts = processor.block_prompts(mock_document)
        assert len(prompts) == 1
        assert "Image description: A test chart description" in prompts[0]["prompt"]

def test_llm_summary_processor_few_shot_prompt(processor, mock_document):
    text_block = MagicMock(spec=Block)
    text_block.ignore_for_output = False
    text_block.removed = False
    text_block.raw_text.return_value = "Normal text content"
    text_block.page_id = 0
    text_block.block_id = 1
    
    mock_document.pages = [MagicMock()]
    mock_document.pages[0].contained_blocks.return_value = [text_block]
    
    prompts = processor.block_prompts(mock_document)
    assert len(prompts) == 1
    prompt_text = prompts[0]["prompt"]
    
    assert "*Input (Text):*" in prompt_text
    assert "*Input (Table):*" in prompt_text
    assert "*Input (Image/Figure Description):*" in prompt_text
    assert "Normal text content" in prompt_text
