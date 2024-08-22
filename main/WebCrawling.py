from selenium.common.exceptions import NoSuchElementException
from dateutil.relativedelta import relativedelta
from main.CustomSelenium import CustomSelenium
from main.ExcelManager import ExcelManager
from datetime import datetime
import time
import re
import os

class WebCrawling:
    def __init__(self, keyword, months=1):
        self.driver = CustomSelenium()
        self.file_manager = ExcelManager('output/files/news.xlsx')
        self.driver.set_webdriver()
        self.keyword = keyword
        self.months = months

    def main_task(self):
        self.go_to_website()
        self.fill_search_field()
        self.process_search_results()
        self.file_manager.close()
        print("Done.")

    def go_to_website(self):
        self.driver.open_url("https://www.reuters.com")

    def fill_search_field(self):
        search_icon = self.driver.find_element_by_css_selector("[aria-label='Open search bar']")
        search_icon.click()
        search_input = self.driver.find_element_by_css_selector("[data-testid='FormField:input']")
        search_input.send_keys(self.keyword)
        send_search_button = self.driver.find_element_by_css_selector("[aria-label='Search']")
        send_search_button.click()
        self.driver.implicitly_wait(5)

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
            print("No news found.")
            return
        for item in news:
            date =  self.driver.find_element_in_element(item, "time").get_attribute("datetime")[:10]
            print("Date: ", date)
            if not self.is_date_in_range(date):
                print("Date out of range, stopping search.")
                break
            else:
                print("Date in range, processing news.")

            title = self.driver.find_element_in_element(
                item, "[data-testid='Heading']"
            ).text
            print("Title:" + title)

            try:
                picture_element = self.driver.find_element_in_element(
                    item, "img"
                )
                picture_filename = os.path.basename(picture_element.get_attribute("src"))
                self.download_picture(picture_element, picture_filename)
                print("Picture filename:" + picture_filename)
            except NoSuchElementException:
                print("Picture filename: None")
                picture_filename = "None"

            try:
                category = self.driver.find_element_in_element(
                    item, "[data-testid='Label']"
                ).text
                print("Category:" + category)
            except NoSuchElementException:
                print("Category: None")
                category = "None"

            hit_count = title.lower().count("nubank")
            print("Hit count:" + str(hit_count))

            has_money_in_title = self.money_regex(title)
            print("Has money in title:" + str(has_money_in_title))

            self.file_manager.write_to_row([title, date, category, picture_filename, hit_count, has_money_in_title])

        else:
            print("Page completed, checking next page.")
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
                print("No more pages to check.")
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
