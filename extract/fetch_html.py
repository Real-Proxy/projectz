# extract/fetch_html.py

import json
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def extract_html(url, output_path="output/raw_input.json"):
    print(f"Launching headless browser to fetch: {url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)

    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Extract readable content
        content = []
        for tag in soup.find_all(["p", "pre", "code", "li", "h1", "h2", "h3", "span"]):
            text = tag.get_text(strip=True)
            if text and len(text) > 3:
                content.append(text)

        # Extract tables
        tables = []
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            rows = []
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if cells:
                    rows.append(cells)
            if headers or rows:
                tables.append({"headers": headers, "rows": rows})

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({"content": content, "tables": tables}, f, indent=2)

        print(f"HTML content saved to: {output_path}")
    except Exception as e:
        print(f"Failed to extract HTML from {url}: {e}")
        os.makedirs("output", exist_ok=True)
        with open("logs/fetch_errors.log", "w") as log:
            log.write(f"[ERROR] {str(e)}\n")
    finally:
        driver.quit()
