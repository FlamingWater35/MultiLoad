from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import concurrent.futures
import requests
from urllib.parse import urljoin


target_url = "https://server.elscione.com/Officially Translated Light Novels/A Certain Magical Index/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

session = requests.Session()
session.headers.update(headers)


def fetch_rendered_html(url):
    try:
        driver = uc.Chrome(headless=True, use_subprocess=False)
    except Exception as e:
        print(f"Initializing ChromeDriver failed: {e}")

    try:
        driver.get(url)

        print("Waiting for page to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(5)

        rendered_html = driver.page_source
        with open("rendered_page.html", "w", encoding="utf-8") as f:
            f.write(rendered_html)
        print("Saved rendered HTML to rendered_page.html")

        return rendered_html
    except Exception as e:
        print(f"Fetching HTML caused an exception: {e}")
    finally:
        if driver:
            driver.quit()


def extract_epub_links(html_page, base_url):
    soup = BeautifulSoup(html_page, "html.parser")
    epub_links = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.lower().endswith(".epub"):
            full_url = urljoin(base_url, href)
            epub_links.append(full_url)

    return epub_links


def get_links():
    if os.path.exists("rendered_page.html"):
        with open("rendered_page.html", "r", encoding="utf-8") as f:
            html = f.read()
        epub_links = extract_epub_links(html, target_url)
        print(f"Found {len(epub_links)} EPUB links")
        return epub_links
    print("HTML page not found")
    return None


replacements = {
    "%20": " ",
    "%5B": "[",
    "%5D": "]",
}


def download_epub(url, save_folder="downloads", max_retries=3):
    global replacements

    os.makedirs(save_folder, exist_ok=True)
    filename = url.split("/")[-1]
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    save_path = os.path.join(save_folder, filename)

    for attempt in range(max_retries):
        if not os.path.exists(save_path):
            try:
                time.sleep(1)
                response = session.get(url, stream=True)

                if response.status_code == 503:
                    print(
                        f"503 Service Unavailable for {filename}. Retrying ({attempt + 1}/{max_retries})..."
                    )
                    time.sleep(2)
                    continue

                response.raise_for_status()

                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)

                print(f"Downloaded: {filename}")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {filename}: {e}")
                if attempt == max_retries - 1:
                    print(
                        f"Failed to download {filename} after {max_retries} attempts."
                    )
        else:
            print(f"File already exists: {filename}")


def download_process(epub_urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(download_epub, epub_urls)


def main():
    fetch_rendered_html(target_url)
    links = get_links()
    if links != None and len(links) >= 1:
        download_process(links)


if __name__ == "__main__":
    main()
