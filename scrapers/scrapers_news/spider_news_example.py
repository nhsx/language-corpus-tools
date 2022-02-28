import datetime
import scrapy
from scrapy.linkextractors import LinkExtractor

from corpus.items import HTMLItem
from corpus.util import BaseNewsSpider


class ExampleTrustNewsSpider(BaseNewsSpider, scrapy.Spider):
    name = "example_trust_news"
    custom_settings = {}

    source_id = "example_trust_news"

    start_urls = ["https://www.EXAMPLETRUSTSITE.nhs.uk/news"]

    link_extractor = LinkExtractor(
        allow=r"^https://www.EXAMPLETRUSTSITE.nhs.uk/news/",
        restrict_css="div.post",
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url, self.parse_item, meta={"dont_refresh": True}
            )

        older = response.css("a.older-posts::attr(href)").get()
        if older is not None:
            yield response.follow(older, self.parse)

    def parse_item(self, response):
        html = response.css("div.text").get()
        if html:
            yield HTMLItem(
                html=html,
                source_url=response.url,
                modified_at=datetime.datetime.now(),
            )
        else:
            self.logger.info(
                "Could not extract any text from %s", response.url
            )
