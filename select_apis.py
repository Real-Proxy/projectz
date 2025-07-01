# select_apis.py

import json
import os

INPUT_PATH = "output/extracted_endpoints.json"
OUTPUT_PATH = "output/selected_apis.json"

def load_endpoints(path=INPUT_PATH):
    if not os.path.exists(path):
        print("extracted_endpoints.json not found.")
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_selected(endpoints, path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(endpoints, f, indent=2)
    print(f"{len(endpoints)} API(s) saved to {path}")

def display_menu(endpoints):
    print("\nAvailable API Endpoints:\n")
    for idx, ep in enumerate(endpoints, 1):
        print(f"[{idx}] {ep['name']} ({ep['method']} {ep['path']})")

def get_selection(max_index):
    raw = input("\nSelect APIs by number (comma-separated, e.g., 1,3,5): ").strip()
    selected = []
    for val in raw.split(","):
        val = val.strip()
        if val.isdigit():
            idx = int(val)
            if 1 <= idx <= max_index:
                selected.append(idx - 1)
    return selected

def run():
    endpoints = load_endpoints()
    if not endpoints:
        return

    display_menu(endpoints)
    selection = get_selection(len(endpoints))
    
    if not selection:
        print("No valid selections made.")
        return

    chosen = [endpoints[i] for i in selection]
    save_selected(chosen)

if __name__ == "__main__":
    run()
