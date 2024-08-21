from robocorp.tasks import task
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
@task
def news_obtainer(keyword, months=1):
    """
    This task will search for news on Reuters website based on a keyword and a date range.
    It will save the news to an Excel file and download the pictures.
    """
    workbook = xlsxwriter.Workbook("output/news.xlsx")
    worksheet = workbook.add_worksheet()
    start_x = 0
    start_y = 0
    main_task()

def main_task():
    go_to_website()
    fill_search_field()
    wait_for_captcha()
    process_search_results()
    workbook.close()
    print("Done.")

def go_to_website():
    selenium.open_url("https://www.reuters.com")

def fill_search_field():
    search_icon = selenium.find_element_by_css_selector("[aria-label='Open search bar']")
    search_icon.click()
    search_input = selenium.find_element_by_css_selector("[data-testid='FormField:input']")
    search_input.send_keys(keyword)
    send_search_button = selenium.find_element_by_css_selector("[aria-label='Search']")
    send_search_button.click()
    selenium.implicitly_wait(5)

def wait_for_captcha():
    captcha_detected = True
    while captcha_detected:
        try:
            captcha = selenium.find_element_by_css_selector("div[class*='captcha']")
            print("Captcha detected, awaiting manual input")
            time.sleep(5)
        except:
            captcha_detected = False
            print("Captcha bypassed")

def process_search_results():
    # in order:
    # 1: check if the news is inside the specified date range, if so, save it to the excel file
    # 2: check if the news has a picture, if so, download it
    # 3: if news list ended and date range not reached, click on the next page button
    # 4: repeat 1-3 until date range is reached
    # beating the lazy load problem
    lazy_loader()
    selenium.implicitly_wait(5)
    process_individual_news()

def lazy_loader():
    y = 1000
    for timer in range(0, 5):
        selenium._driver.execute_script("window.scrollTo(0, " + str(y) + ")")
        y += 1000
        time.sleep(0.5)

def is_date_in_range(date):
    today = datetime.today()
    range = today + relativedelta(months=-months)

    if datetime.strptime(date, "%Y-%m-%d") >= range:
        return True
    return False

def process_individual_news():
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
        if not is_date_in_range(date):
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
            donwload_picture(picture_element, picture_filename)
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

        has_money_in_title = money_regex(title)
        print("Has money in title:" + str(has_money_in_title))
        add_to_xlsx(title, date, category, picture_filename, hit_count, has_money_in_title)
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
            process_search_results()
        except NoSuchElementException:
            print("No more pages to check.")
            return

def add_to_xlsx( title, date, category, picture_filename, hit_count, has_money_in_title):
    worksheet.write(start_x, start_y, title)
    worksheet.write(start_x, start_y + 1, date)
    worksheet.write(start_x, start_y + 2, category)
    worksheet.write(start_x, start_y + 3, picture_filename)
    worksheet.write(start_x, start_y + 4, hit_count)
    worksheet.write(start_x, start_y + 5, has_money_in_title)
    start_x += 1

def money_regex(title):
    # this regex checks whether the sentence has money in the following formats:
    # $11.11, $111,111.11, 11 dollars, 11 USD
    # I am going to be profoundly honest here: I hate regex, I wont lose too much time on this.
    pattern = r"\$\d+(,\d{3})*(\.\d{2})?|\d+\s(dollars|USD)"
    result = re.findall(pattern, title)
    if result == []:
        return False
    return True

def donwload_picture( element, filename):
    with open("output/" + filename, "wb") as file:
        file.write(element.screenshot_as_png)
