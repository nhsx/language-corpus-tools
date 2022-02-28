import os
from html.parser import HTMLParser
from io import StringIO
from abc import ABC

import scrapy, scrapy.logformatter

class BaseNewsSpider(ABC):
    doccano_project_id = int(os.environ["DOCCANO_PROJECT_ID_NEWS"])
    medcat_dataset_id = int(2)

class QuietLogFormatter(scrapy.logformatter.LogFormatter):
    def scraped(self, item, response, spider):
        return (
            super().scraped(item, response, spider)
            if spider.settings.getbool("LOG_SCRAPED_ITEMS")
            else None
        )

    def dropped(self, item, exception, response, spider):
        return (
            super().scraped(item, exception, response, spider)
            if spider.settings.getbool("LOG_DROPPED_ITEMS")
            else None
        )

class HTMLMarkupStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_tags(html):
    s = HTMLMarkupStripper()
    s.feed(html)
    return s.get_data()