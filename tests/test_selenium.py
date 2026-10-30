import os
import shutil
import time
import socket
import threading
import pytest
from werkzeug.serving import make_server
from app import create_app
from app.config import TestConfig
from app.database import db

# Check if selenium package is installed
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerThread(threading.Thread):
    def __init__(self, app, port):
        super().__init__()
        self.server = make_server("127.0.0.1", port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def get_chrome_binary():
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def get_chromedriver_binary():
    candidates = [
        shutil.which("chromedriver"),
        shutil.which("chromium.chromedriver"),
        "/opt/homebrew/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/usr/bin/chromedriver",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


@pytest.fixture
def browser():
    """
    Initializes and yields a headless Chrome webdriver lazily when a test executes.
    If Chrome or ChromeDriver is unavailable, skips gracefully with a clear reason.
    Ensures WebDriver is properly closed using driver.quit() on teardown.
    """
    if not SELENIUM_AVAILABLE:
        pytest.skip("Selenium package is not installed in the environment.")

    chrome_bin = get_chrome_binary()
    if not chrome_bin:
        pytest.skip("Chrome/Chromium browser binary is not installed or available on this system.")

    driver_bin = get_chromedriver_binary()
    if not driver_bin:
        pytest.skip("ChromeDriver executable is not installed or available on PATH.")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin

    service = Service(executable_path=driver_bin)

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options, service=service)
    except Exception as exc:
        pytest.skip(f"Failed to initialize Chrome WebDriver: {exc}")

    try:
        yield driver
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


@pytest.fixture(scope="module")
def live_server():
    """Starts a live Flask server running the test configuration on an ephemeral port."""
    app = create_app(TestConfig)
    port = find_free_port()
    server_thread = ServerThread(app, port)
    server_thread.start()
    time.sleep(0.5)  # allow server to start

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server_thread.shutdown()
    server_thread.join()


def test_selenium_registration_and_login_flow(browser, live_server):
    """
    End-to-end browser test using Selenium:
    1. Navigate to /register and submit user details.
    2. Confirm redirection to /login with flash success.
    3. Log in with newly created credentials.
    4. Verify dashboard loads with user session.
    """
    # 1. Registration
    browser.get(f"{live_server}/register")
    assert "Sign Up" in browser.title or "ExpenseTrack" in browser.title

    browser.find_element(By.ID, "username").send_keys("selenium_user")
    browser.find_element(By.ID, "email").send_keys("selenium@example.com")
    browser.find_element(By.ID, "password").send_keys("Password123")
    browser.find_element(By.ID, "confirm_password").send_keys("Password123")
    browser.find_element(By.ID, "submit").click()

    # 2. Confirm redirect to login
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "username_or_email")))
    assert "Sign In" in browser.page_source or "login" in browser.current_url

    # 3. Log In
    browser.find_element(By.ID, "username_or_email").send_keys("selenium_user")
    browser.find_element(By.ID, "password").send_keys("Password123")
    browser.find_element(By.ID, "submit").click()

    # 4. Confirm Dashboard loaded
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "metric-value")))
    assert "Financial Overview" in browser.page_source
    assert "selenium_user" in browser.page_source


def test_selenium_add_transaction(browser, live_server):
    """
    Browser test:
    1. Log in.
    2. Navigate to /transactions/new.
    3. Fill out and submit transaction.
    4. Verify presence in transaction list.
    """
    # Log in first
    browser.get(f"{live_server}/login")
    browser.find_element(By.ID, "username_or_email").send_keys("selenium_user")
    browser.find_element(By.ID, "password").send_keys("Password123")
    browser.find_element(By.ID, "submit").click()

    # Navigate to add transaction
    browser.get(f"{live_server}/transactions/new")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "amount")))

    browser.find_element(By.ID, "amount").send_keys("88.50")
    browser.find_element(By.ID, "description").send_keys("Selenium E2E Test Expense")
    browser.find_element(By.ID, "submit").click()

    # Verify transaction in list
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    assert "Selenium E2E Test Expense" in browser.page_source
    assert "88.50" in browser.page_source
