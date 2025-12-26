from google import genai
import os
from pydantic import BaseModel

class SummarySchema(BaseModel):
    analysis: str
    summary: str

client = genai.Client(api_key=API_KEY)

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=["Summarize this in one sentence: The quick brown fox jumps over the lazy dog."],
        config={
            "response_mime_type": "application/json",
            "response_schema": SummarySchema
        }
    )
    print(response.candidates[0].content.parts[0].text)
except Exception as e:
    print(f"Error: {e}")
