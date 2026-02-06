import os
import google.generativeai as genai
from typing import Generator

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def stream_gemini_completion_sync(prompt: str) -> Generator[str, None, None]:
    """
    Synchronous Gemini token stream.
    """
    response = model.generate_content(prompt, stream=True)

    for chunk in response:
        if chunk.text:
            yield chunk.text

