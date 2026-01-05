import os
from google import genai

def get_gemini_client():
    return genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY")
    )
