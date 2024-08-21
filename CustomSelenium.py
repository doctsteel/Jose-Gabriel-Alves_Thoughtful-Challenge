from selenium.webdriver import ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class CustomSelenium:
    def set_webdriver(self):
        self._driver = webdriver.Chrome()
        self._driver.set_window_position(0, 0)
        print("WebDriver initialized successfully.")

    def set_page_size(self, width: int, height: int):
        # Extract the current window size from the driver
        current_window_size = self._driver.get_window_size()

        # Extract the client window size from the html tag
        html = self._driver.find_element_by_tag_name("html")
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = width + (current_window_size["width"] - inner_width)
        target_height = height + (current_window_size["height"] - inner_height)
        self._driver.set_window_rect(width=target_width, height=target_height)

    def open_url(self, url: str, screenshot: str = None):
        self._driver.get(url)
        if screenshot:
            self._driver.get_screenshot_as_file(screenshot)

    def driver_quit(self):
        if self._driver:
            self._driver.quit()

    def full_page_screenshot(self, url):
        self._driver.get(url)
        page_width = self._driver.execute_script("return document.body.scrollWidth")
        page_height = self._driver.execute_script("return document.body.scrollHeight")
        self._driver.set_window_size(page_width, page_height)
        self._driver.save_screenshot("screenshot.png")
        self._driver.quit()

    def implicitly_wait(self, seconds: int):
        self._driver.implicitly_wait(seconds)

    def find_element_by_css_selector(self, css_selector: str) -> WebElement:
        return self._driver.find_element(By.CSS_SELECTOR, css_selector)
    
    def find_elements(self, css_selector: str) -> list[WebElement]:
        return self._driver.find_elements(By.CSS_SELECTOR, css_selector)
    
    def find_element_by_tag_name(self, tag_name: str) -> WebElement:
        return self._driver.find_element(By.TAG_NAME, tag_name)
    
    def find_element_in_element(self, element: WebElement, css_selector: str) -> WebElement:
        return element.find_element(By.CSS_SELECTOR, css_selector)

cs = CustomSelenium()
