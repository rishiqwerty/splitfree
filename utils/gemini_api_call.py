import os
from google import genai
from google.genai import types
from google.api_core.exceptions import DeadlineExceeded # type: ignore
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_content(requested_content):
    # Generate content using the Gemini model
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-8b", contents=f"{requested_content}",
            config=types.GenerateContentConfig(
        max_output_tokens=500,
        temperature=0.1,
        system_instruction="You are an expense manager. Your name is splitfree.",
    )

        )
        return response.text
    except DeadlineExceeded:
        return "The request timed out. Please try again later."