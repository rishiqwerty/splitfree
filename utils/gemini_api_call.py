import os
import requests
from google import genai
from google.genai import types
from google.api_core.exceptions import DeadlineExceeded  # type: ignore

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
use_local_llm = os.getenv("USE_LOCAL_LLM")
llm_url = os.getenv("LOCAL_LLM_URL")
llm_model = os.getenv("LLM_MODEL")


def generate_content(requested_content):
    # Generate content using the Gemini model
    try:
        if use_local_llm:
            response = requests.post(
                llm_url,
                json={
                    "model": llm_model,
                    "prompt": f"{requested_content}",
                    "stream": False,
                    "options": {
                        "max_new_tokens": 300,
                        "num_thread": 1,
                    },
                },
            )
            return response.json().get("response", "")
        else:
            response = client.models.generate_content(
                model="gemini-1.5-flash-8b",
                contents=f"{requested_content}",
                config=types.GenerateContentConfig(
                    max_output_tokens=500,
                    temperature=0.1,
                    system_instruction="You are an expense manager. Your name is splitfree.",
                ),
            )
            return response.text
    except DeadlineExceeded:
        return "The request timed out. Please try again later."
