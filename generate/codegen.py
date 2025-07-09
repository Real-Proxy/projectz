import os
import json
import re

SELECTED_FILE = "output/selected_apis.json"
OUTPUT_FILE = "output/generated_code.go"

IMPORTS = '''package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)
'''

BASE_URL = "https://api.example.com"

# ---------------- Templates ----------------

GET_TEMPLATE = '''func {{FUNC_NAME}}({{PARAMS}}) (*http.Response, error) {
    baseURL := "{{BASE_URL}}{{PATH}}"
    reqURL := fmt.Sprintf("%s?{{QUERY_STRING}}", baseURL{{ARGS}})
    req, err := http.NewRequest("{{METHOD}}", reqURL, nil)
    if err != nil {
        return nil, err
    }

    {{HEADERS}}

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }

    defer resp.Body.Close()
    return resp, nil
}'''

POST_LIKE_TEMPLATE = '''func {{FUNC_NAME}}({{PARAMS}}) (*http.Response, error) {
    url := fmt.Sprintf("{{BASE_URL}}{{PATH}}"{{ARGS}})
    payload := map[string]interface{}{
        {{BODY_KV_PAIRS}}
    }

    jsonData, err := json.Marshal(payload)
    if err != nil {
        return nil, err
    }

    req, err := http.NewRequest("{{METHOD}}", url, bytes.NewBuffer(jsonData))
    if err != nil {
        return nil, err
    }

    req.Header.Set("Content-Type", "application/json")
    {{HEADERS}}

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }

    defer resp.Body.Close()
    return resp, nil
}'''

# ---------------- Helpers ----------------

used_func_names = {}

def pascal_case(name):
    return ''.join(word.capitalize() for word in re.sub(r'[^a-zA-Z0-9]', ' ', name).split())

def get_unique_func_name(base_name):
    base = pascal_case(base_name)
    count = used_func_names.get(base, 0)
    used_func_names[base] = count + 1
    return base if count == 0 else f"{base}{count+1}"

def sanitize(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)

def build_headers_code(headers):
    if not headers:
        return ""
    return '\n    '.join([f'req.Header.Set("{h}", "<{h.lower()}-value>")' for h in headers])

def extract_path_params(path):
    return re.findall(r"[<{]([a-zA-Z0-9_]+)[>}]?", path)

def replace_path_placeholders(path):
    return re.sub(r"[<{]([a-zA-Z0-9_]+)[>}]?", "%s", path)

# ---------------- Codegen Logic ----------------

def generate_get_or_delete_function(ep, method):
    func_name = get_unique_func_name(ep.get("name", "CallApi"))
    param_list = ep.get("parameters", [])
    path_params = extract_path_params(ep.get("path", ""))
    query_params = [p["name"] for p in param_list if p.get("in") == "query"]
    all_param_names = path_params + query_params
    args = ', '.join([sanitize(p) + ' string' for p in all_param_names])
    fmt_args = ', ' + ', '.join([sanitize(p) for p in path_params]) if path_params else ''
    query_string = '&'.join([f'{p}=%s' for p in query_params])
    query_fmt_args = ', ' + ', '.join([sanitize(p) for p in query_params]) if query_params else ''
    headers = build_headers_code(ep.get("headers", []))
    final_args = fmt_args + query_fmt_args

    code = GET_TEMPLATE \
        .replace("{{FUNC_NAME}}", func_name) \
        .replace("{{PARAMS}}", args) \
        .replace("{{BASE_URL}}", BASE_URL) \
        .replace("{{PATH}}", replace_path_placeholders(ep.get("path", ""))) \
        .replace("{{QUERY_STRING}}", query_string) \
        .replace("{{ARGS}}", final_args) \
        .replace("{{HEADERS}}", headers) \
        .replace("{{METHOD}}", method)
    return code

def generate_post_put_function(ep):
    func_name = get_unique_func_name(ep.get("name", "CallApi"))
    req_body = ep.get("request_body", {})
    path_params = extract_path_params(ep.get("path", ""))
    body_kv = ',\n        '.join([f'"{k}": {sanitize(k)}' for k in req_body.keys()])
    args = ', '.join([f'{sanitize(k)} string' for k in list(path_params) + list(req_body.keys())])
    fmt_args = ', ' + ', '.join([sanitize(p) for p in path_params]) if path_params else ''
    headers = build_headers_code(ep.get("headers", []))

    code = POST_LIKE_TEMPLATE \
        .replace("{{FUNC_NAME}}", func_name) \
        .replace("{{PARAMS}}", args) \
        .replace("{{BODY_KV_PAIRS}}", body_kv) \
        .replace("{{METHOD}}", ep.get("method", "POST").upper()) \
        .replace("{{PATH}}", replace_path_placeholders(ep.get("path", ""))) \
        .replace("{{BASE_URL}}", BASE_URL) \
        .replace("{{HEADERS}}", headers) \
        .replace("{{ARGS}}", fmt_args)
    return code

def generate_go_code():
    if not os.path.exists(SELECTED_FILE):
        raise FileNotFoundError("selected_apis.json not found.")

    with open(SELECTED_FILE, "r") as f:
        endpoints = json.load(f)

    if not endpoints:
        raise ValueError("No endpoints found in selected_apis.json")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        f.write(IMPORTS + "\n")

        for ep in endpoints:
            method = ep.get("method", "GET").upper()
            if method in ["GET", "DELETE"]:
                code = generate_get_or_delete_function(ep, method)
            elif method in ["POST", "PUT"]:
                code = generate_post_put_function(ep)
            else:
                continue

            f.write("\n" + code + "\n")

    print(f"Code generated at: {OUTPUT_FILE}")
    return endpoints
