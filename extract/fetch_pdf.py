# extract/fetch_pdf.py

import fitz  # PyMuPDF
import json
import os

def extract_pdf(pdf_path, output_path="output/raw_input.json"):
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return

    try:
        doc = fitz.open(pdf_path)
        content = []

        print(f"Extracting text from: {pdf_path} ({len(doc)} pages)")

        for page in doc:
            text = page.get_text("text").strip()
            if text:
                content.append(text)

        doc.close()

        output_data = {
            "content": content,
            "tables": []  # Consistent with HTML output
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"PDF content saved to: {output_path}")

    except Exception as e:
        print(f"Failed to extract PDF: {e}")
