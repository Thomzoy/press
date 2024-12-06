import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse


def setup_headless_browser():
    """Set up Chrome in headless mode"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--remote-debugging-pipe')
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    # chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    # chrome_options.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})

    driver = webdriver.Chrome(options=chrome_options)

    return driver


def login_and_navigate(
    url,
    username,
    password,
    next_pages,
    fcts=[],
):
    """
    Automate login and page navigation

    :param url: Initial login page URL
    :param username: Login username
    :param password: Login password
    :param target_page: URL of page to navigate after login
    :return: None
    """
    # Decode the URL
    decoded_url = urllib.parse.unquote(url)

    try:
        # Setup headless browser
        driver = setup_headless_browser()

        # Navigate to login page
        driver.get(decoded_url)

        # Wait for login form to load (customize selectors as needed)
        wait = WebDriverWait(driver, 10)

        # Find and fill username field
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        username_field.send_keys(username)

        # Find and fill password field
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)

        # Submit login form
        submit_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
        submit_button.click()

        # Wait for login to complete
        wait.until(EC.url_changes(decoded_url))

        for i, next_page in enumerate(next_pages):
            # Navigate to target page
            driver.get(next_page)

            # Optional: Add additional interaction or data extraction here

            # Example: Print current page title
            print(f"Current Page Title: {driver.title}")
        for fct in fcts:
            fct(driver)

    except Exception as e:
        print(f"An login error occurred: {e}")
        traceback.print_exc()

    return driver
