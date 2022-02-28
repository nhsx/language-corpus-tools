import json
import os
import datetime
import dateutil.parser
from io import StringIO

import scrapy

from corpus.items import HTMLItem

class ItemQueue:
    """This class is used to make sure the Items are ordered by the documents' modification time."""
    def __init__(self):
        self.start_pos = 0
        self.queue = []
        self.size = 0
        self.next_page_url = None

    def put(self, idx, item):
        idx -= self.start_pos
        if idx < 0:
            raise Exception("Item has already been processed")
        if idx >= len(self.queue):
            self.queue.extend([None] * (idx - len(self.queue) + 1))
        if self.queue[idx] is not None:
            raise Exception("Item is already set")
        self.queue[idx] = item

    def poll(self):
        while self.queue and self.queue[0] is not None:
            self.start_pos += 1
            yield self.queue.pop(0)

    def is_empty(self):
        return self.start_pos == self.size


class NHSConditionsAPISpider(scrapy.Spider):
    name = "nhs_conditions"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1,
        "REDIRECT_ENABLED": False,
        "HTTPERROR_ALLOW_ALL": True, # It is important that the response callback is always called, even if there was an error, to update the item queue.
    }

    # This attribute is used to identify the source from which a document was downloaded. It is mandatory and should be unique (however nothing breaks if
    # it isn't). Currently it's mostly for information purposes (it goes into the source_id column of the documents table), it's not used by business logic.
    source_id = name

    doccano_project_id = int(os.environ["DOCCANO_PROJECT_ID_COND"])
    medcat_dataset_id = int(1)

    api_key = os.environ["NHS_API_KEY"]
    headers = {"subscription-key": api_key}

    @staticmethod
    def extract_text_from_main_entity(ent, text=None):
        if text is None:
            text = StringIO()
        for elt in ent:
            nested = elt.get("mainEntityOfPage")
            if elt.get("name") == "markdown":
                text.write(elt.get("text"))
            if isinstance(nested, list):
                NHSConditionsAPISpider.extract_text_from_main_entity(nested, text)
        return text

    def start_requests(self):
        # In order to support incremental scraping we need to know the modification date of the last imported item.
        # The framework sets it as the last_modified attribute of the spider, however start_requests is called before the engine is started
        # so at this point the attibute won't be set.
        # To overcome this we issue a dummy request first. By the time the callback (the parse method) is called the engine will have started and
        # the last_modified attribute will have been set.
        return [scrapy.Request(url="file:///dev/null")]

    def parse(self, response):
        query = "order=oldest&orderBy=dateModified"
        if hasattr(self, "last_modified"):
            date_str = self.last_modified.strftime("%Y-%m-%d")
            query += f"&startDate={date_str}"

        return [
            scrapy.Request(
                url="https://api.nhs.uk/conditions/?" + query,
                headers=self.headers,
                callback=self.parse_index,
            )
        ]

    def parse_index(self, response):
        rjson = json.loads(response.text)
        next_page_url = None
        for link in rjson["relatedLink"]:
            if link["name"] == "Next Page":
                next_page_url = link["url"]
                break
        item_queue = ItemQueue()
        links = rjson["significantLink"]
        requests = []
        for link in links:
            rel = link["linkRelationship"]
            if rel == "Result":
                req = scrapy.Request(
                    link["url"],
                    self.parse_item,
                    headers=self.headers,
                    meta={
                        "item_queue": item_queue,
                        "position": len(requests),
                        "force_refresh": True,
                    },
                )
                req.priority = -len(requests)
                requests.append(req)
        if requests:
            item_queue.size = len(requests)
            item_queue.next_page_url = next_page_url
            return requests
        if next_page_url is not None:
            return [
                scrapy.Request(next_page_url, self.parse_index, headers=self.headers)
            ]
        return []

    def parse_item(self, response):
        meta = response.request.meta
        if response.status == 200:
            rjson = json.loads(response.text)
            try:
                html = self.__class__.extract_text_from_main_entity(
                    rjson["mainEntityOfPage"]
                ).getvalue()
            except KeyError:
                html = ""
            item = HTMLItem(
                html=html,
                source_url=response.url,
                retrieved_at=datetime.datetime.now(),
                modified_at=dateutil.parser.parse(rjson["dateModified"]),
            )
        else:
            item = HTMLItem(
                html="", source_url=response.url, retrieved_at=datetime.datetime.now()
            )
            self.logger.info(
                f"Response code for {response.url} is {response.status}. Skipping..."
            )
        item_queue = meta["item_queue"]
        item_queue.put(meta["position"], item)
        for item in item_queue.poll():
            if item.get("html") != "":
                yield item
            else:
                url = item.get("source_url")
                self.logger.warn("Could not extract any text from %s", url)
        if item_queue.is_empty() and item_queue.next_page_url is not None:
            yield scrapy.Request(
                item_queue.next_page_url, self.parse_index, headers=self.headers
            )
