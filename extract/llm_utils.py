# extract/llm_utils.py

import json
import re

def chunk_text(text, max_chars=4000):
    """
    Splits a large string into smaller chunks that do not exceed `max_chars` length.
    Useful for feeding data safely into LLMs.
    """
    chunks = []
    current_chunk = []
    current_len = 0

    for line in text.splitlines():
        if current_len + len(line) > max_chars:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(line)
        current_len += len(line)

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def is_valid_json_array(text):
    """
    Checks if the given string is a valid JSON array.
    """
    try:
        data = json.loads(text)
        return isinstance(data, list)
    except json.JSONDecodeError:
        return False

def extract_json_blocks(text):
    """
    Extracts all valid JSON array blocks from a messy LLM output.
    Useful when models return arrays with leading or trailing text.
    """
    blocks = []
    pattern = re.compile(r"\[\s*{.*?}\s*\]", re.DOTALL)

    for match in pattern.findall(text):
        try:
            parsed = json.loads(match)
            if isinstance(parsed, list):
                blocks.append(json.dumps(parsed))
        except json.JSONDecodeError:
            continue

    return blocks

def deduplicate_endpoints(endpoints):
    """
    Deduplicates endpoints based on (method, path) tuple.
    """
    seen = set()
    unique = []

    for ep in endpoints:
        key = (ep.get("method"), ep.get("path"))
        if key not in seen:
            seen.add(key)
            unique.append(ep)

    return unique
