from robocorp.tasks import task
from main.EnvConfig import EnvConfig
from main.WebCrawling import WebCrawling

@task
def news_obtainer():
    """
    This task will search for news on Reuters website based on a keyword and a date range.
    It will save the news to an Excel file and download the pictures.
    """
    configs = EnvConfig()
    keyword = configs.get_keyword()
    months = configs.get_months()
    crawler = WebCrawling(keyword, months)
    crawler.main_task()
