from CustomSelenium import CustomSelenium
from selenium.common.exceptions import NoSuchElementException
import time
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
import os

selenium = CustomSelenium()
selenium.set_webdriver()

class NewsObtainer:
    def __init__(self, keyword, months=1):
        self.keyword = keyword
        self.months = months
        self.workbook = xlsxwriter.Workbook("output/news.xlsx")
        self.worksheet = self.workbook.add_worksheet()
        self.start_x = 0
        self.start_y = 0

    def main_task(self):
        self.go_to_website()
        self.fill_search_field()
        self.wait_for_captcha()
        self.process_search_results()
        self.workbook.close()
        print("Done.")

    def go_to_website(self):
        selenium.open_url("https://www.reuters.com")

    def fill_search_field(self):
        search_icon = selenium.find_element_by_css_selector("[aria-label='Open search bar']")
        search_icon.click()
        search_input = selenium.find_element_by_css_selector("[data-testid='FormField:input']")
        search_input.send_keys(self.keyword)
        send_search_button = selenium.find_element_by_css_selector("[aria-label='Search']")
        send_search_button.click()
        selenium.implicitly_wait(5)

    def wait_for_captcha(self):
        captcha_detected = True
        while captcha_detected:
            try:
                captcha = selenium.find_element_by_css_selector("div[class*='captcha']")
                print("Captcha detected, awaiting manual input")
                time.sleep(5)
            except:
                captcha_detected = False
                print("Captcha bypassed")

    def process_search_results(self):
        # in order:
        # 1: check if the news is inside the specified date range, if so, save it to the excel file
        # 2: check if the news has a picture, if so, download it
        # 3: if news list ended and date range not reached, click on the next page button
        # 4: repeat 1-3 until date range is reached
        # beating the lazy load problem
        self.lazy_loader()
        selenium.implicitly_wait(5)
        self.process_individual_news()

    def lazy_loader(self):
        y = 1000
        for timer in range(0, 5):
            selenium._driver.execute_script("window.scrollTo(0, " + str(y) + ")")
            y += 1000
            time.sleep(0.5)

    def is_date_in_range(self, date):
        today = datetime.today()
        range = today + relativedelta(months=-self.months)

        if datetime.strptime(date, "%Y-%m-%d") >= range:
            return True
        return False

    def process_individual_news(self):
        news = selenium.find_elements('li[class^="search-results__item"]')
        if not news:
            print("No news found")
            return
        for item in news:
            # time.sleep(0.5)
            # check if the news is inside the specified date range
            date = selenium.find_element_in_element(
                item, "time"
            ).get_attribute("datetime")[:10]
            print("Date:" + date)
            if not self.is_date_in_range(date):
                print("Date out of range, stopping search")
                break
            else:
                print("Date in range, continuing search")

            # process title, date, category, pic filename, hit count, money boolean and save it to excel file

            title = selenium.find_element_in_element(
                item, "[data-testid='Heading']"
            ).text
            print("Title:" + title)            

            try:
                picture_element = selenium.find_element_in_element(
                    item, "img"
                )
                picture_filename = os.path.basename(picture_element.get_attribute("src"))
                self.donwload_picture(picture_element, picture_filename)
                print("Picture filename:" + picture_filename)
            except NoSuchElementException:
                print("Picture filename: None")
                picture_filename = "None"

            try:
                category = selenium.find_element_in_element(
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
            self.add_to_xlsx(title, date, category, picture_filename, hit_count, has_money_in_title)
        else:
            print("Completed one page. Checking for next page.")
            try:
                next_page = selenium.find_element_by_css_selector(
                    "[aria-label^='Next stories']"
                )
                selenium._driver.execute_script(
                    "arguments[0].scrollIntoView();", next_page
                )
                selenium._driver.execute_script(
                    "window.scrollTo(0, window.scrollY - 300)"
                )
                time.sleep(5)
                next_page.click()
                selenium.implicitly_wait(5)
                self.process_search_results()
            except NoSuchElementException:
                print("No more pages to check.")
                return

    def add_to_xlsx(self, title, date, category, picture_filename, hit_count, has_money_in_title):
        self.worksheet.write(self.start_x, self.start_y, title)
        self.worksheet.write(self.start_x, self.start_y + 1, date)
        self.worksheet.write(self.start_x, self.start_y + 2, category)
        self.worksheet.write(self.start_x, self.start_y + 3, picture_filename)
        self.worksheet.write(self.start_x, self.start_y + 4, hit_count)
        self.worksheet.write(self.start_x, self.start_y + 5, has_money_in_title)
        self.start_x += 1

    def money_regex(self, title):
        # this regex checks whether the sentence has money in the following formats:
        # $11.11, $111,111.11, 11 dollars, 11 USD
        # I am going to be profoundly honest here: I hate regex, I wont lose too much time on this.
        pattern = r"\$\d+(,\d{3})*(\.\d{2})?|\d+\s(dollars|USD)"
        result = re.findall(pattern, title)
        if result == []:
            return False
        return True

    def donwload_picture(self, element, filename):
        with open("output/" + filename, "wb") as file:
            file.write(element.screenshot_as_png)
# def test_money_regex():
#     title1 = "Nubank raised 11 dollars in funding"
#     title2 = "Nubank raised $11.11 in funding"
#     title3 = "Nubank raised $111,111.11 in funding"
#     title4 = "Nubank raised 11 USD in funding"
#     title5 = "lol lmao"

#     print(money_regex(title1))
#     print(money_regex(title2))
#     print(money_regex(title3))
#     print(money_regex(title4))
#     print(money_regex(title5))

if __name__ == "__main__":
    #test_money_regex()
    news = NewsObtainer("Nubank", 24)
    news.main_task()
