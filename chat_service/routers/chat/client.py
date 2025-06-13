# deps/openai_client.py
from openai import OpenAI
import os

# Singleton client instance
openai_client = OpenAI()

def get_openai_client() -> OpenAI:
    return openai_client(
        base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"),  # Make sure `/v1` is included
        api_key=os.getenv("OPENAI_API_KEY", "lm-studio")  # Example: use env var; ensure 'os' is imported
    )  # Optionally pass in API keys, config, etc.