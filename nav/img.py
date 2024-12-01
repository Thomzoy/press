from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import time
import base64
import os
from bs4 import BeautifulSoup
import json
import pandas as pd
from pathlib import Path

BASE_PATH = Path("journals")


class src_change(object):
    def __init__(self, locator, src):
        self.locator = locator
        self.src = src

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        actual_src = element.get_attribute('src')
        if actual_src != self.src:
            return element
        else:
            return False

def get_images(driver, journal_id, wait_time=10, limit=-1, do_screenshot=False):

    journal_url = f'https://nouveau-europresse-com.bnf.idm.oclc.org/Pdf/Edition?sourceCode={journal_id}'
    driver.get(journal_url)

    # Locate button that opens page list side-panel
    panel_btn = WebDriverWait(driver, wait_time).until(
        EC.element_to_be_clickable(
            (By.CLASS_NAME, 'pdf-pages-panel-btn')
        )
    )

    # Open page list side-panel
    panel_btn.click()

    # Wait until all page links are visible
    pdf_page_spans = WebDriverWait(driver, wait_time).until(
        EC.presence_of_all_elements_located(
            (By.CLASS_NAME, 'pdf-page')
        )
    )

    print(f"Number of pages: {len(pdf_page_spans)}")

    img_src = ""

    for page_index, span in enumerate(pdf_page_spans):
        if page_index<16:
            continue
        print(f"Getting page {page_index}")

        try:
            parent_li = span.find_element(By.XPATH, './ancestor::li')
            parent_li = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable(parent_li)
            )
            parent_li.click()

            if do_screenshot:
                screenshot_path = (BASE_PATH / f"{journal_id}/screenshots")
                screenshot_path.mkdir(parents=True, exist_ok=True)
                driver.save_screenshot(screenshot_path / f"{page_index}.png")

            images = WebDriverWait(driver, wait_time).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, 'viewer-move')
                )
            )
            assert len(images)==1

            wait = WebDriverWait(driver, 10)
            img = wait.until(
                src_change(
                    (By.CLASS_NAME, 'viewer-move'), 
                    img_src
                )
            )

            #img = images[0]
            img_src = img.get_attribute('src')
            assert img_src and img_src.startswith('data:image/png;base64,')

            base64_data = img_src.split(',')[1]
            image_path = (BASE_PATH / f"{journal_id}/images")
            image_path.mkdir(parents=True, exist_ok=True)
            image_path = image_path / f'{page_index}.png'

            # Decode and save the image
            with open(image_path, 'wb') as file:
                file.write(base64.b64decode(base64_data))

            if (limit > 0) and (page_index >= limit):
                break
        except Exception as e:
            print("Page error: ", e)
