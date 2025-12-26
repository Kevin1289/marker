from typing import List
from pydantic import BaseModel

from marker.logger import get_logger
from marker.processors.llm import PromptData, BaseLLMSimpleBlockProcessor, BlockData
from marker.schema import BlockTypes
from marker.schema.document import Document

logger = get_logger()

class SummarySchema(BaseModel):
    analysis: str
    summary: str

class LLMSummaryProcessor(BaseLLMSimpleBlockProcessor):
    block_types = (
        BlockTypes.SectionHeader,
        BlockTypes.Text,
        BlockTypes.TableGroup,
        BlockTypes.ListGroup,
        BlockTypes.Code,
        BlockTypes.Equation,
        BlockTypes.Form,
        BlockTypes.ComplexRegion,
        BlockTypes.FigureGroup,
        BlockTypes.PictureGroup,
    )

    summary_prompt = """You are an expert at summarizing document content for downstream LLM analysis.
Your goal is to provide a descriptive but concise summary of the following document block.

**Examples:**

*Input (Text):*
"The company reported a 15% increase in revenue for Q3, reaching $4.2 billion. This growth was primarily driven by strong sales in the cloud services division, which grew by 22% year-over-year. Operating margins also improved from 18% to 20%."
*Output:*
This block discusses the financial performance of a company for Q3. Revenue increased 15% to $4.2 billion, led by a 22% growth in cloud services, while operating margins improved to 20%.

*Input (Table):*
| Category | 2022 Sales | 2023 Sales | Change |
|----------|------------|------------|--------|
| Laptops  | 1200       | 1500       | +25%   |
| Tablets  | 800        | 750        | -6.25% |
| Phones   | 3000       | 3200       | +6.7%  |
*Output:*
The content is a sales comparison table for different electronics categories between 2022 and 2023. It shows growth in laptops (+25%) and phones (+6.7%), while tablet sales saw a slight decline of 6.25%.

*Input (Image/Figure Description):*
"Image description: A line chart titled 'Monthly Active Users' showing a steady upward trend from January (2M) to December (5.5M) 2023. The steeper growth is visible from June onwards."
*Output:*
This content describes a line chart showing monthly active user growth in 2023. Users increased from 2M in January to 5.5M in December, with growth accelerating after June.

**Content to summarize:**
{context}

**Guidelines:**
- Be descriptive but concise.
- Limit the summary to exactly 3 sentences maximum.
- If the content is a table, do NOT include all data points. Instead, provide representative examples of the data contained.
- The summary will be used by another LLM to answer questions about the document.

**Instructions:**
1. Analyze the content provided.
2. Provide a 1-2 sentence analysis of what the content is.
3. Provide a summary (max 3 sentences) that captures the core information.
"""

    def block_prompts(self, document: Document) -> List[PromptData]:
        prompt_data = []
        for block_data in self.inference_blocks(document):
            block = block_data["block"]
            
            if block.ignore_for_output or block.removed:
                continue

            # Get the content of the block
            context = block.raw_text(document).strip()
            
            # Use description for figures/pictures if raw text is empty
            if (not context or len(context) < 10) and hasattr(block, "description") and block.description:
                context = f"Image description: {block.description}"

            if not context:
                continue

            # Prepare the prompt
            prompt = self.summary_prompt.format(context=context[:2000]) # Limit context length

            prompt_data.append({
                "prompt": prompt,
                "image": None, # No image for summary to save costs
                "block": block,
                "schema": SummarySchema,
                "page": block_data["page"]
            })
        return prompt_data

    def rewrite_block(self, response: dict, prompt_data: PromptData, document: Document):
        block = prompt_data["block"]

        if not response or "summary" not in response:
            block.update_metadata(llm_error_count=1)
            return

        summary = response["summary"].strip()
        if len(summary) < 5:
            block.update_metadata(llm_error_count=1)
            return

        block.summary = summary
