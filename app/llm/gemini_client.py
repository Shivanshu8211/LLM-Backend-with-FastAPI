import os
import google.generativeai as genai
from typing import AsyncGenerator

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


async def stream_gemini_completion(prompt: str) -> AsyncGenerator[str, None]:
    """
    Native Gemini token streaming.
    Falls back gracefully if streaming fails.
    """
    try:
        response = model.generate_content(
            prompt,
            stream=True
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        # Fallback: non-streaming response
        full_response = model.generate_content(prompt)
        yield full_response.text
