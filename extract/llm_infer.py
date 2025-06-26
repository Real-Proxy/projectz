# extract/llm_infer.py

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def extract_api_endpoints(cleaned_path="output/cleaned_input.json", raw_output_path="output/llm_output.txt"):
    if not os.path.exists(cleaned_path):
        print(f"[ERROR] Cleaned input file not found: {cleaned_path}")
        return

    with open(cleaned_path, "r") as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    print(f"[INFO] Loaded {len(chunks)} chunks for DeepSeek inference")

    os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)

    with open(raw_output_path, "w") as out_file:
        for i, chunk in enumerate(chunks, start=1):
            prompt = f"""
You are an API documentation extractor.

Analyze the input and extract all REST API endpoints in the following strict JSON format:

{{
  "endpoints": [
    {{
      "method": "HTTP_METHOD",
      "path": "/full/api/path",
      "description": "Short functional description",
      "parameters": ["param1", "param2"],
      "request_body": {{
        "field1": "type",
        "field2": "type"
      }},
      "headers": ["Header1", "Header2"]
    }}
  ]
}}

Rules:
1. Include all endpoints mentioned in the documentation
2. Only use GET, POST, PUT, DELETE
3. Always start path with `/`
4. Description should be concise (3–7 words)
5. List all parameters in order of appearance
6. Use [] for parameters if none
7. Use {{}} for request_body if none
8. Use [] for headers if none
9. Output only valid JSON — no markdown, no explanations
10. Wrap your result in: {{ "endpoints": [...] }}

--- START CHUNK {i} ---
{chunk}
--- END CHUNK {i} ---
"""

            print(f"[INFO] Sending chunk {i}/{len(chunks)} to DeepSeek...")
            time.sleep(1)  # Rate limit safety

            try:
                payload = {
                    "model": TOGETHER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.2
                }

                response = requests.post(TOGETHER_URL, headers=HEADERS, json=payload)
                response.raise_for_status()

                result = response.json()["choices"][0]["message"]["content"].strip()

                out_file.write(f"\n# --- Chunk {i} ---\n")
                out_file.write(result + "\n")

            except Exception as e:
                print(f"[ERROR] Failed chunk {i}: {e}")
                out_file.write(f"\n# --- Chunk {i} ERROR ---\n{e}\n")

    print(f"[INFO] Raw LLM output saved to: {raw_output_path}")
