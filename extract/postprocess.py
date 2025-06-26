# extract/postprocess.py

import json
import os
from .llm_utils import deduplicate_endpoints

RAW_INPUT_PATH = "output/llm_output.txt"
OUTPUT_JSON_PATH = "output/extracted_endpoints.json"

def extract_all_endpoint_blocks(text):
    """
    Extracts all JSON blocks that contain an 'endpoints' key.
    Handles multiple chunks in a raw LLM output file.
    """
    endpoints = []
    chunks = text.split("# --- Chunk")

    for chunk in chunks:
        if "{" not in chunk:
            continue
        try:
            json_start = chunk.index("{")
            candidate = chunk[json_start:]
            data = json.loads(candidate)
            if isinstance(data, dict) and "endpoints" in data:
                endpoints.extend(data["endpoints"])
        except Exception:
            continue

    return endpoints

def normalize_endpoint(ep):
    return {
        "name": ep.get("description", "").strip(),
        "method": ep.get("method", "").strip().upper(),
        "path": ep.get("path", "").strip(),
        "description": ep.get("description", "").strip(),
        "parameters": [
            {
                "name": p,
                "type": "string",
                "required": False,
                "in": "query"
            } for p in ep.get("parameters", [])
        ],
        "request_body": ep.get("request_body", {}),
        "headers": ep.get("headers", [])
    }

def parse_llm_output(raw_path=RAW_INPUT_PATH, out_path=OUTPUT_JSON_PATH):
    print(f"Parsing LLM output from: {raw_path}")

    if not os.path.exists(raw_path):
        print("LLM output file missing.")
        return

    with open(raw_path, "r") as f:
        raw_text = f.read()

    raw_endpoints = extract_all_endpoint_blocks(raw_text)
    print(f"Found {len(raw_endpoints)} raw endpoints across all chunks")

    if not raw_endpoints:
        print("No valid endpoint data found.")
        return

    cleaned = [normalize_endpoint(ep) for ep in raw_endpoints]
    cleaned = deduplicate_endpoints(cleaned)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Parsed {len(cleaned)} endpoints")
    print(f"Saved to: {out_path}")

if __name__ == "__main__":
    parse_llm_output()
