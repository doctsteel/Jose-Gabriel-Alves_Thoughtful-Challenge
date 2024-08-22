from selenium.common.exceptions import NoSuchElementException
from dateutil.relativedelta import relativedelta
from main.CustomSelenium import CustomSelenium
from main.ExcelManager import ExcelManager
from datetime import datetime
import logging
import time
import sys
import re
import os

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("webcrawling.log"), logging.StreamHandler()],
)


class WebCrawling:
    def __init__(self, keyword, months=1):
        self.driver = CustomSelenium()
        self.file_manager = ExcelManager('output/news.xlsx')
        self.driver.set_webdriver()
        self.keyword = keyword
        self.months = months
        self.logger = logging.getLogger(self.__class__.__name__)

    def main_task(self):
        self.go_to_website()
        self.fill_search_field()
        self.process_search_results()
        self.file_manager.close()
        self.logger.info("Done.")

    def go_to_website(self):
        self.driver.open_url("https://www.reuters.com", "output/website.png")
        self.logger.info("Website opened. Sleeping for a minute.")

    def fill_search_field(self):
        self.driver.implicitly_wait(10)
        try:
            search_icon = self.driver.find_element_by_css_selector("[aria-label='Open search bar']")
            search_icon.click()
            search_input = self.driver.find_element_by_css_selector("[data-testid='FormField:input']")
            search_input.send_keys(self.keyword)
            send_search_button = self.driver.find_element_by_css_selector("[aria-label='Search']")
            send_search_button.click()
            self.driver.implicitly_wait(5)
        except NoSuchElementException:
            self.logger.info("We've been blocked. Stopping search.")
            sys.exit(1)
            return
    
    def process_search_results(self):
        # in order:
        # 1: check if the news is inside the specified date range, if so, save it to the excel file
        # 2: check if the news has a picture, if so, download it
        # 3: if news list ended and date range not reached, click on the next page button
        # 4: repeat 1-3 until date range is reached

        self.lazy_loader()
        self.driver.implicitly_wait(5)
        self.process_individual_news()

    def lazy_loader(self):
        y = 1000
        for timer in range(0, 5):
            self.driver._driver.execute_script("window.scrollTo(0, " + str(y) + ")")
            y += 1000
            time.sleep(0.5)

    def is_date_in_range(self, date):
        today = datetime.today()
        range = today + relativedelta(months=-self.months)
        if datetime.strptime(date, "%Y-%m-%d") >= range:
            return True
        return False

    def process_individual_news(self):
        # find the list of search results
        news = self.driver.find_elements('li[class^="search-results__item"]')
        if not news:
            self.logger.info("No news found.")
            return
        for item in news:
            date =  self.driver.find_element_in_element(item, "time").get_attribute("datetime")[:10]
            self.logger.info("Date: ", date)
            if not self.is_date_in_range(date):
                self.logger.debug("Date out of range, stopping search.")
                break
            else:
                self.logger.debug("Date in range, processing news.")

            title = self.driver.find_element_in_element(
                item, "[data-testid='Heading']"
            ).text
            self.logger.info("Title:" + title)

            try:
                picture_element = self.driver.find_element_in_element(
                    item, "img"
                )
                picture_filename = os.path.basename(picture_element.get_attribute("src"))
                self.download_picture(picture_element, picture_filename)
                self.logger.info("Picture filename:" + picture_filename)
            except NoSuchElementException:
                self.logger.info("Picture filename: None")
                picture_filename = "None"

            try:
                category = self.driver.find_element_in_element(
                    item, "[data-testid='Label']"
                ).text
                self.logger.debug("Category:" + category)
            except NoSuchElementException:
                self.logger.debug("Category: None")
                category = "None"

            hit_count = title.lower().count("nubank")
            self.logger.debug("Hit count:" + str(hit_count))

            has_money_in_title = self.money_regex(title)
            self.logger.debug("Has money in title:" + str(has_money_in_title))

            self.file_manager.write_to_row([title, date, category, picture_filename, hit_count, has_money_in_title])

        else:
            self.logger.info("Page completed, checking next page.")
            try:
                next_page = self.driver.find_element_by_css_selector(
                    "[aria-label^='Next stories']"
                )
                self.driver._driver.execute_script(
                    "arguments[0].scrollIntoView();", next_page
                )
                self.driver._driver.execute_script(
                    "window.scrollTo(0, window.scrollY - 300)"
                )
                time.sleep(5)
                next_page.click()
                self.driver.implicitly_wait(5)
                self.process_search_results()
            except NoSuchElementException:
                self.logger.info("No more pages to check.")
                return
            

    def download_picture(self, element, filename):
        with open('output/files/' + filename, 'wb') as file:
            file.write(element.screenshot_as_png)

    def money_regex(self, title):
        # this regex checks whether the sentence has money in the following formats:
        # $11.11, $111,111.11, 11 dollars, 11 USD
        # I am going to be profoundly honest here: I hate regex, I wont lose too much time on this.
        pattern = r"\$\d+(,\d{3})*(\.\d{2})?|\d+\s(dollars|USD)"
        result = re.findall(pattern, title)
        if result == []:
            return False
        return True
