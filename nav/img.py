from datetime import datetime
from pathlib import Path
import traceback
import time
import base64
from typing import Literal

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from dateparser import DateDataParser

# from .pdf import make_pdf
from .journals import JOURNAL_URL

BASE_PATH = Path("journals").resolve()


class src_change(object):
    def __init__(self, locator, src):
        self.locator = locator
        self.src = src

    def __call__(self, driver: WebDriver):
        # element = driver.find_element(*self.locator)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(self.locator)
        )
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(self.locator)
        )

        actual_src = element.get_attribute("src")
        if actual_src != self.src:
            return element
        else:
            return False


def get_existing_images(images_path: Path):
    print(f"Finding pages in {images_path}")
    pages = [int(path.stem) for path in images_path.glob("*.png")]
    return set(pages)


class Images:
    def __init__(
        self,
        driver: WebDriver,
        journal_id,
        wait_time=10,
        limit=-1,
        do_screenshot=False,
        overwrite=False,
        existing_dates=[],
    ):
        self.driver = driver
        self.journal_id = journal_id
        self.wait_time = wait_time
        self.limit = limit
        self.do_screenshot = do_screenshot
        self.overwrite = overwrite
        self.existing_dates = existing_dates

        self.base_images_path = BASE_PATH / f"{journal_id}/images"

        self.screenshot_path = BASE_PATH / f"{journal_id}/screenshots"
        self.screenshot_path.mkdir(parents=True, exist_ok=True)

        self.journal_url = JOURNAL_URL.format(journal_id=journal_id)
        self.all_saved = True
        self.date = None

    def run(self, n_try=1) -> Literal["skip", "done", "miss"]:
        for i in range(n_try):
            print(f"Try n°{i+1} of {n_try}")
            result = self._get_images()
            if result in ["done", "skip"]:
                return result
        return result

    def _get_images(self) -> Literal["skip", "done", "miss"]:
        self.driver.get(self.journal_url)

        # Get date
        date_span = WebDriverWait(self.driver, self.wait_time).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "pdf-source-name"))
        )

        soup = BeautifulSoup(
            date_span.get_attribute("outerHTML"),
            "html.parser",
        )
        weekday_span = soup.find("span", class_="pdf-source-weekday")
        # Get the text after the weekday span
        if weekday_span:
            ddp = DateDataParser(languages=["fr"])
            date = weekday_span.next_sibling.strip()
            date = ddp.get_date_data(date).date_obj
            print(date_span.text)
        else:
            date = datetime.now()

        self.date = date.strftime("%Y-%m-%d")
        self.images_path = self.base_images_path / self.date
        self.images_path.mkdir(parents=True, exist_ok=True)

        if self.date in self.existing_dates:
            print(f"Edition from {self.journal_id} / {self.date} already saved !")
            return "skip"

        existing_images = (
            set() if self.overwrite else get_existing_images(self.images_path)
        )
        print(f"Existing pages: {existing_images}")

        # Locate button that opens page list side-panel
        panel_btn = WebDriverWait(self.driver, self.wait_time).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "pdf-pages-panel-btn"))
        )

        # Open page list side-panel
        panel_btn.click()

        # Wait until all page links are visible
        pdf_page_spans = WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "pdf-page"))
        )

        self.n_pages = len(pdf_page_spans)

        print(f"Number of pages: {self.n_pages}")
        pdf_page_spans = [
            (idx + 1, span)
            for idx, span in enumerate(pdf_page_spans)
            if idx + 1 not in existing_images
        ]
        print(f"Number of unsaved pages: {len(pdf_page_spans)}")

        if not pdf_page_spans:
            self.all_saved = True
            print("All pages are saved, skipping scraping !")
            return "done"

        img_src = ""

        for page_index, span in pdf_page_spans:
            print(f"Getting page {page_index}")
            if page_index in existing_images:
                print("Page already exists, skipping")
                continue

            try:
                parent_li = span.find_element(By.XPATH, "./ancestor::li")
                print(parent_li.is_displayed())
                self.driver.save_screenshot(self.screenshot_path / "before_scroll.png")
                # time.sleep(5)
                # driver.save_screenshot(screenshot_path / f"before_scroll_5s.png")
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", parent_li
                )
                self.driver.save_screenshot(self.screenshot_path / "after_scroll.png")
                time.sleep(2)
                self.driver.save_screenshot(
                    self.screenshot_path / "after_scroll_2s.png"
                )
                # #print(parent_li.is_displayed())
                # #driver.save_screenshot(screenshot_path / f"after_scroll.png")
                parent_li = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of(parent_li)
                )
                parent_li = WebDriverWait(self.driver, self.wait_time).until(
                    EC.element_to_be_clickable(parent_li)
                )
                parent_li.click()

                if self.do_screenshot:
                    self.driver.save_screenshot(
                        self.screenshot_path / f"{page_index}.png"
                    )

                images = WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "viewer-move"))
                )
                assert len(images) == 1

                img = self.driver.find_element(By.CLASS_NAME, "viewer-move")
                n_try = 0
                while img.get_attribute("src") == img_src:
                    print(f"Try n° {n_try}")
                    time.sleep(2)
                    img = self.driver.find_element(By.CLASS_NAME, "viewer-move")
                    n_try += 1
                    if n_try > 5:
                        print("No source change")
                        continue

                # wait = WebDriverWait(driver, 10)
                # img = wait.until(
                #     src_change(
                #         (By.CLASS_NAME, 'viewer-move'),
                #         img_src
                #     )
                # )

                # img = images[0]
                time.sleep(5)
                img = self.driver.find_element(By.CLASS_NAME, "viewer-move")
                img_src = img.get_attribute("src")
                assert img_src and img_src.startswith("data:image/png;base64,")

                base64_data = img_src.split(",")[1]
                image_path = self.images_path / f"{page_index}.png"

                # Decode and save the image
                with open(image_path, "wb") as file:
                    file.write(base64.b64decode(base64_data))

                if (self.limit > 0) and (page_index >= self.limit):
                    break
            except Exception as e:
                print(traceback.format_exc())
                print("Page error: ", e)

        existing_images = get_existing_images(self.images_path)
        if self.n_pages == len(existing_images):
            self.all_saved = True
            print("All pages are saved, skipping scraping !")
            return "done"
        else:
            missing_pages = [
                (idx, span)
                for (idx, span) in pdf_page_spans
                if idx not in existing_images
            ]
            print(f"{len(missing_pages)} pages are missing: {missing_pages}")
            self.all_saved = False
            return "miss"
