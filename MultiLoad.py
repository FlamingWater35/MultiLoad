from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import concurrent.futures
import requests
from urllib.parse import urljoin
import dearpygui.dearpygui as dpg
import time
import os
import sys
import logging
import ctypes
import pywinstyles
from win32 import win32gui


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


# "https://server.elscione.com/Officially Translated Light Novels/A Certain Magical Index/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

session = requests.Session()
session.headers.update(headers)
epub_links_list: list = []
progress_bars: list = []

replacements = {
    "%20": " ",
    "%5B": "[",
    "%5D": "]",
}


def fetch_rendered_html(url):
    try:
        driver = uc.Chrome(headless=True, use_subprocess=False)
    except Exception as e:
        logging.error(f"Driver initializing error: {e}")
        add_text_to_log(f"Driver initializing error: {e}")

    try:
        driver.get(url)

        logging.info("Waiting for page to load...")
        add_text_to_log("Waiting for page to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)
        rendered_html = driver.page_source
        logging.info("Page source found, getting links...")
        add_text_to_log("Page source found, getting links...")

        epub_links = extract_epub_links(rendered_html, url)
        logging.info(f"Found {len(epub_links)} EPUB links")
        add_text_to_log(f"Found {len(epub_links)} EPUB links")

        return epub_links

    except Exception as e:
        logging.info(f"Fetching HTML caused an exception: {e}")
    finally:
        if driver:
            driver.quit()


def extract_epub_links(html_page, base_url):
    soup = BeautifulSoup(html_page, "html.parser")
    epub_links: list = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.lower().endswith(".epub"):
            full_url = urljoin(base_url, href)
            epub_links.append(full_url)

    return epub_links


def download_epub(url, save_folder, progress_bar_tag, max_retries=3):
    global session, replacements

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
                    logging.info(
                        f"503 Service Unavailable for {filename}. Retrying ({attempt + 1}/{max_retries})..."
                    )
                    add_text_to_download_log(
                        f"503 Service Unavailable for {filename}. Retrying ({attempt + 1}/{max_retries})..."
                    )
                    time.sleep(2)
                    continue

                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                update_progress_bar(progress_bar_tag, 0, total_size, 0.0)

                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        downloaded += len(chunk)
                        progress = downloaded / total_size if total_size > 0 else 0
                        update_progress_bar(
                            progress_bar_tag, downloaded, total_size, progress
                        )

                logging.info(f"Downloaded: {filename}")
                add_text_to_download_log(f"Downloaded: {filename}")
                break
            except Exception as e:
                logging.info(f"Attempt {attempt + 1} failed for {filename}: {e}")
                add_text_to_download_log(
                    f"Attempt {attempt + 1} failed for {filename}: {e}"
                )
                if attempt == max_retries - 1:
                    logging.error(
                        f"Failed to download {filename} after {max_retries} attempts."
                    )
                    add_text_to_download_log(
                        f"Failed to download {filename} after {max_retries} attempts."
                    )
        else:
            logging.info(f"File already exists: {filename}")
            add_text_to_download_log(f"File already exists: {filename}")
            file_size = os.path.getsize(save_path)
            update_progress_bar(progress_bar_tag, file_size, file_size, 1.0)


def download_process(epub_urls):
    if epub_urls and len(epub_urls) >= 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for url in epub_urls:
                pb_tag = f"pb_{url.split('/')[-1]}_{time.time()}"
                futures.append(
                    executor.submit(download_wrapper, url, "downloads", pb_tag)
                )
            concurrent.futures.wait(futures)
    else:
        logging.info("No download links found")
        add_text_to_download_log("No download links found")


"""def show_install_popup(self, e):
    (title=f"Initializing ChromeDriver failed: {e}", message="Do you want to download Chrome? (Yes/No)", icon="question", option_2="No", option_1="Yes", border_width=4, border_color="#43A047", fade_in_duration=50, justify="center")
    if msg.get() == "Yes":
        webbrowser.open("https://www.google.com/chrome/")"""


def add_text_to_log(text: str):
    dpg.add_text(text, parent="get_links_log", wrap=0)


def add_text_to_download_log(text: str):
    dpg.add_text(text, parent="download_log", wrap=0)


def download_wrapper(url, save_folder, pb_tag):
    try:
        spacer_ids = create_progress_bar(pb_tag)
        download_epub(url, save_folder, pb_tag)
    except Exception as e:
        logging.error(f"Download failed: {e}")
        add_text_to_download_log(f"Download failed: {e}")
    finally:
        delete_progress_bar(pb_tag, spacer_ids)


def create_progress_bar(pb_tag):
    item_id = dpg.add_spacer(height=5, parent="progress_bars_container")
    dpg.add_progress_bar(
        tag=pb_tag,
        default_value=0.0,
        width=-5,
        height=40,
        show=True,
        parent="progress_bars_container",
        overlay="0.0 MB / 0.0 MB (0%)",
    )
    item2_id = dpg.add_spacer(height=5, parent="progress_bars_container")

    return (item_id, item2_id)


def delete_progress_bar(pb_tag, spacer_ids):
    if dpg.does_item_exist(pb_tag):
        dpg.delete_item(pb_tag)
    for spacer_id in spacer_ids:
        if dpg.does_item_exist(spacer_id):
            dpg.delete_item(spacer_id)


def update_progress_bar(progress_bar_tag, downloaded, total_size, progress):
    downloaded_mb = downloaded / (1024 * 1024)
    if total_size > 0:
        total_mb = total_size / (1024 * 1024)
        overlay = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({progress * 100:.0f}%)"
    else:
        overlay = f"{downloaded_mb:.1f} MB / ??? MB (Unknown)"
    dpg.set_value(progress_bar_tag, progress)
    dpg.configure_item(progress_bar_tag, overlay=overlay)


def start_downloads(sender, app_data):
    global epub_links_list

    dpg.disable_item("download_buttons_group")
    dpg.show_item("progress_bars_container")
    dpg.show_item("download_log")
    dpg.hide_item("links_list")
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(download_process, epub_links_list)
    future.add_done_callback(on_downloads_complete)


def on_downloads_complete(future):
    dpg.hide_item("progress_bars_container")
    dpg.hide_item("download_log")
    dpg.show_item("links_list")
    dpg.enable_item("download_buttons_group")
    print("\nDownloads complete!")


def get_links_button_press(sender, app_data):
    url = dpg.get_value("url_input")
    if url != None and "https:/" in url:
        dpg.disable_item("get_links_button")
        dpg.disable_item("url_input")
        dpg.show_item("get_links_log")
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(fetch_rendered_html, url)
        future.add_done_callback(on_fetch_complete)


def on_fetch_complete(future):
    global epub_links_list

    dpg.enable_item("get_links_button")
    dpg.enable_item("url_input")
    dpg.show_item("links_list")

    try:
        epub_links = future.result()
        epub_links_list = epub_links
    except Exception as e:
        logging.error(f"Error: {e}")
        add_text_to_log(f"Error: {e}")

    dpg.set_value("links_found_label", f"Links found: {len(epub_links_list)}")
    for index in range(len(epub_links_list)):
        link_name = epub_links_list[index].split("/")[-1]
        for old, new in replacements.items():
            link_name = link_name.replace(old, new)
        dpg.add_selectable(label=f"{link_name}", parent="links_list")
        dpg.add_spacer(height=5, parent="links_list")
    dpg.show_item("download_buttons_group")


def setup_ui():
    global epub_links_list, progress_bars

    with dpg.font_registry(tag="font_registry"):
        font_size = 26
        custom_font = dpg.add_font(resource_path("docs/font.otf"), font_size)

    logging.debug("Image initialized")

    with dpg.theme() as child_window_theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 15, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3, 3)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 4, 4)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (93, 64, 55))
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 5)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 2, 2)
        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 5)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 2, 2)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (93, 64, 55))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (200, 200, 200, 100))
        with dpg.theme_component(dpg.mvProgressBar):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 2, 2)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (183, 28, 28))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 53, 147))
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (27, 94, 32))
        with dpg.theme_component(dpg.mvInputText):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 6)
        with dpg.theme_component(dpg.mvInputText, enabled_state=False):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 6)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (93, 64, 55))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (200, 200, 200, 100))
        with dpg.theme_component(dpg.mvSelectable):
            dpg.add_theme_color(dpg.mvThemeCol_Header, (200, 100, 0, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (220, 100, 0, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (180, 120, 50, 200))
        with dpg.theme_component(dpg.mvCollapsingHeader):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 5)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 96, 100))
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 2, 2)

    with dpg.theme() as main_window_theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_Border, (21, 101, 192))

    dpg.bind_font(custom_font)
    logging.debug("Font bound to main window")

    try:
        with dpg.window(tag="main_window"):
            with dpg.tab_bar(reorderable=True):
                with dpg.tab(label="Fetch links"):
                    with dpg.child_window(
                        autosize_x=True,
                        auto_resize_y=True,
                        tag="multiload_main_window_1",
                    ):
                        dpg.add_text("Add url of a website:", wrap=0)
                        dpg.add_spacer(height=5)
                        dpg.add_input_text(
                            tag="url_input",
                            width=-5,
                            hint="Paste your url here",
                        )
                        dpg.add_spacer(height=10)
                        dpg.add_button(
                            label="Get links",
                            callback=get_links_button_press,
                            tag="get_links_button",
                        )
                        dpg.add_spacer(height=10)

                        with dpg.child_window(
                            tag="get_links_log", auto_resize_y=True, show=False
                        ):
                            pass
                        dpg.add_spacer(height=10)

                with dpg.tab(label="Download files"):
                    with dpg.child_window(
                        autosize_x=True,
                        auto_resize_y=True,
                        tag="multiload_main_window_2",
                    ):
                        dpg.add_text("Links found: 0", wrap=0, tag="links_found_label")
                        dpg.add_spacer(height=10)

                        with dpg.group(
                            horizontal=True, show=False, tag="download_buttons_group"
                        ):
                            dpg.add_button(
                                label="Download all", callback=start_downloads
                            )
                            dpg.add_spacer(width=10)
                            dpg.add_button(label="Download selected")

                        dpg.add_spacer(height=5)
                        with dpg.child_window(
                            tag="progress_bars_container",
                            auto_resize_y=True,
                            show=False,
                        ):
                            pass

                        dpg.add_spacer(height=5)
                        with dpg.child_window(
                            tag="links_list", auto_resize_y=True, show=False
                        ):
                            pass
                        dpg.add_spacer(height=5)

                        with dpg.child_window(
                            tag="download_log", auto_resize_y=True, show=False
                        ):
                            pass
                        dpg.add_spacer(height=10)

        dpg.bind_item_theme("main_window", child_window_theme)
        dpg.bind_item_theme("multiload_main_window_1", main_window_theme)
        dpg.bind_item_theme("multiload_main_window_2", main_window_theme)
        dpg.bind_item_theme("get_links_log", main_window_theme)
        dpg.bind_item_theme("links_list", main_window_theme)
        dpg.bind_item_theme("progress_bars_container", main_window_theme)
        dpg.set_primary_window("main_window", True)

    except Exception as e:
        logging.critical(f"Setting up primary window and/or themes failed: {e}")


def main():
    dpg.create_context()

    user32 = ctypes.windll.user32
    screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    dpg.create_viewport(
        title="MultiLoad",
        width=int(screen_width / 1.5),
        height=int(screen_height / 1.5),
        vsync=True,
    )
    dpg.set_viewport_small_icon(resource_path("docs/icon.ico"))
    dpg.set_viewport_pos(
        [
            (screen_width / 2) - (dpg.get_viewport_width() / 2),
            (screen_height / 2) - (dpg.get_viewport_height() / 2),
        ]
    )

    setup_ui()
    dpg.setup_dearpygui()
    dpg.show_viewport()

    hwnd = win32gui.FindWindow(None, "MultiLoad")
    if hwnd == 0:
        logging.error("Window not found for pywinstyles")
    else:
        pywinstyles.apply_style(hwnd, "mica")

    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
