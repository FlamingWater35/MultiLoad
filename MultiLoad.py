from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import concurrent.futures
import requests
from urllib.parse import urljoin
import customtkinter as ct
from CTkMessagebox import CTkMessagebox
import time
import os
import sys
import webbrowser
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def resource_path(relative_path):
    # Get the directory of the executable (or script in development)
    if "__compiled__" in globals():  # Check if running as a Nuitka bundle
        base_path = os.path.dirname(sys.executable)  # Executable's directory
    else:
        base_path = os.path.abspath(".")

    full_path = os.path.join(base_path, relative_path)

    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)
        logging.error(f"Resource not found: {full_path}")

    return full_path


class App(ct.CTk):
    def __init__(self):
        super().__init__()

        self.title("MultiLoad")
        window_width = 1000
        window_height = 600

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.iconbitmap(resource_path("docs/icon.ico"))

        ct.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
        ct.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # "https://server.elscione.com/Officially Translated Light Novels/A Certain Magical Index/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.epub_links_list: list = []

        self.replacements = {
            "%20": " ",
            "%5B": "[",
            "%5D": "]",
        }

        self.create_main_ui()


    def create_main_ui(self):
        self.main_frame = ct.CTkFrame(self, border_width=4, corner_radius=10)
        self.main_frame.grid(column=0, row=0, padx=30, pady=30)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure((0, 1, 2), weight=1)

        self.url_entry = ct.CTkEntry(self.main_frame, width=800, placeholder_text="Add url of a website")
        self.url_entry.grid(column=0, row=0, padx=30, pady=(30, 10))

        self.fetch_html_button = ct.CTkButton(self.main_frame, text="Search for links", font=ct.CTkFont(family="Segoe UI"), width=130, command=self.fetch_html_button_start)
        self.fetch_html_button.grid(column=0, row=1, padx=30, pady=10)

        self.event_log = ct.CTkTextbox(self.main_frame, width=500, height=150, font=ct.CTkFont(family="Microsoft JhengHei", size=13), state="disabled")
        self.event_log.grid(column=0, row=2, padx=30, pady=(10, 30))
    

    def add_to_log(self, text: str):
        self.event_log.configure(state="normal")
        self.event_log.insert("end", text + "\n")
        self.event_log.see("end")
        self.event_log.configure(state="disabled")


    def fetch_html_button_start(self):
        self.fetch_html_button.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        
        url = self.url_entry.get()
        if url != None and "https:/" in url:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self.fetch_rendered_html, url)
            future.add_done_callback(self.on_fetch_complete)


    def on_fetch_complete(self, future):
        self.fetch_html_button.configure(state="normal")
        self.url_entry.configure(state="normal")
        
        try:
            epub_links = future.result()
            self.epub_links_list = epub_links
            print(self.epub_links_list)
        except Exception as e:
            self.add_to_log(f"Error: {e}")


    def show_install_popup(self, e):
        msg = CTkMessagebox(title=f"Initializing ChromeDriver failed: {e}", message="Do you want to download Chrome? (Yes/No)", icon="question", option_2="No", option_1="Yes", border_width=4, border_color="#43A047", fade_in_duration=50, justify="center")
        if msg.get() == "Yes":
            webbrowser.open("https://www.google.com/chrome/")


    def fetch_rendered_html(self, url):
        try:
            driver = uc.Chrome(headless=True, use_subprocess=False)
        except Exception as e:
            self.after(0, lambda: self.show_install_popup(e))

        try:
            driver.get(url)

            self.after(0, lambda: self.add_to_log("Waiting for page to load..."))
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(3)
            rendered_html = driver.page_source
            self.after(0, lambda: self.add_to_log("Page source found, getting links..."))

            epub_links = self.extract_epub_links(rendered_html, url)
            self.after(0, lambda: self.add_to_log(f"Found {len(epub_links)} EPUB links"))

            return epub_links
        
        except Exception as e:
            self.after(0, lambda: self.add_to_log(f"Fetching HTML caused an exception: {e}"))
        finally:
            if driver:
                driver.quit()


    def extract_epub_links(self, html_page, base_url):
        soup = BeautifulSoup(html_page, "html.parser")
        epub_links: list = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.lower().endswith(".epub"):
                full_url = urljoin(base_url, href)
                epub_links.append(full_url)

        return epub_links


    def download_epub(self, url, save_folder="downloads", max_retries=3):
        os.makedirs(save_folder, exist_ok=True)
        filename = url.split("/")[-1]
        for old, new in self.replacements.items():
            filename = filename.replace(old, new)
        save_path = os.path.join(save_folder, filename)

        for attempt in range(max_retries):
            if not os.path.exists(save_path):
                try:
                    time.sleep(1)
                    response = self.session.get(url, stream=True)

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


    def download_process(self, epub_urls):
        if epub_urls != None and len(epub_urls) >= 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                executor.map(self.download_epub, epub_urls)
        else:
            print("No download links found")


if __name__ == "__main__":
    app = App()
    app.mainloop()
