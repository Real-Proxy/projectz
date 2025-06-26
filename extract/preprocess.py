# extract/preprocess.py

import json
import os

def preprocess_document(json_path, chunk_size=12000, output_path="output/cleaned_input.json"):
    if not os.path.exists(json_path):
        print(f"[ERROR] JSON file not found: {json_path}")
        return []

    with open(json_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return []

    content = data.get("content", [])
    tables = data.get("tables", [])
    blocks = []

    # Collect textual content blocks
    for item in content:
        text = item.strip()
        if len(text) > 10 and not text.lower().startswith("copyright"):
            blocks.append(text)

    # Extract readable rows from tables
    for table in tables:
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        for row in rows:
            row_text = " | ".join(row).strip()
            if row_text and not row_text.lower().startswith("example"):
                blocks.append(row_text)

    print(f"Filtered {len(blocks)} blocks from documentation")

    # Chunking
    chunks = []
    current_chunk = ""

    for block in blocks:
        if len(current_chunk) + len(block) + 1 <= chunk_size:
            current_chunk += block + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = block + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"chunks": chunks}, f, indent=2)

    print(f"Saved {len(chunks)} cleaned chunks to: {output_path}")
    return chunks
