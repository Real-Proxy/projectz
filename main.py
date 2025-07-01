# main.py

import argparse
import os
import subprocess
from extract.fetch_html import extract_html
from extract.fetch_pdf import extract_pdf
from extract.preprocess import preprocess_document
from extract.llm_infer import extract_api_endpoints

def is_pdf(file_path):
    return file_path.lower().endswith(".pdf")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API Documentation Extractor")
    parser.add_argument("--input", required=True, help="URL or PDF file path")
    args = parser.parse_args()
    input_path = args.input.strip()

    print(f"Input received: {input_path}")

    # Step 1: Extract content
    if input_path.startswith("http"):
        print("Fetching HTML content...")
        extract_html(input_path, output_path="output/raw_input.json")

    elif is_pdf(input_path):
        print("Fetching PDF content...")
        extract_pdf(input_path, output_path="output/raw_input.json")

    else:
        print("Unsupported input type. Provide a URL or a PDF file.")
        exit(1)

    # Step 2: Preprocess and chunk
    print("Preprocessing input...")
    chunks = preprocess_document(
        json_path="output/raw_input.json",
        chunk_size=12000,
        output_path="output/cleaned_input.json"
    )

    if len(chunks) == 0:
        print("No valid content to process. Exiting.")
        exit(0)

    print(f"Saved {len(chunks)} cleaned chunks to: output/cleaned_input.json")

    # Step 3: LLM Inference
    print("Running LLM inference...")
    extract_api_endpoints(
        cleaned_path="output/cleaned_input.json",
        raw_output_path="output/llm_output.txt"
    )

    # Step 4: Postprocess to final JSON
    print("Postprocessing LLM output...")
    subprocess.run(["python", "-m", "extract.postprocess"])
    