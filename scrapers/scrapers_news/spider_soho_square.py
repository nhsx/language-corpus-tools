import re
import datetime

import scrapy

from corpus.items import HTMLItem
from corpus.util import BaseNewsSpider

class SohoSquareReviewsSpider(BaseNewsSpider, scrapy.Spider):
    """An example of multiple documents on one page."""

    name = "SohoSquare"
    custom_settings = {
    }

    source_id = "soho_square_reviews"

    start_urls = ["https://www.nhs.uk/services/gp-surgery/soho-square-general-practice/E87714/ratings-and-reviews"]


    def parse(self, response):
        for item in response.xpath("/html/body//main//div[@aria-label='Organisation review']"):
            headline = item.xpath("div/h3/span/text()[2]").get()
            if not headline:
                self.logger.warning("Could not extract headline from %s", item)
                continue
            headline = headline.strip()

            # This is fiddly, unfortunately the page structure does not provide any more reliable clues, like classes or ids.
            # In practice this means it will break if the page structure changes even slightly.
            text = item.xpath("div/p[4]").get()
            id_link = item.xpath("div/p[6]/a/@href").get()
            m = re.search(r"report\?commentID=([\w-]+)", id_link)
            if not m:
                self.logger.warning("Could not extract comment id from %s", id_link)
                continue
            comment_id = m.group(1)

            # Note, the source_url is formed by adding the review's unique id to the page URL. modified_at is not set.
            # This ensures there are no duplicates.
            yield HTMLItem(html=headline+". "+text, source_url=response.url+"#"+comment_id)
