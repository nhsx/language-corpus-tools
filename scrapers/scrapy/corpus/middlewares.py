# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import os
import time
from scrapy import signals
from scrapy.exceptions import IgnoreRequest, CloseSpider
from txpostgres import txpostgres
from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.internet.defer import ensureDeferred

from corpus import items


class CorpusSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RetryThrottleMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        s.crawler = crawler
        return s

    async def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        if response.status == 429 or response.status == 503:
            try:
                sec = int(response.headers.get("Retry-After"))
            except (TypeError, ValueError):
                sec = 30
            logging.info(
                f"Received a {response.status} response while retrieving {request.url}. Sleeping for {sec} seconds..."
            )
            self.crawler.engine.pause()
            await deferLater(reactor, sec, lambda: None)
            self.crawler.engine.unpause()
            logging.info("Woke up")
            req = request.copy()
            req.dont_filter = True
            return req
        return response


class CorpusDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    async def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        if not hasattr(spider, "db_conn"):
            raise CloseSpider()
        if not request.meta.get("force_refresh"):
            res = await spider.db_conn.runQuery(
                "SELECT modified_at FROM documents WHERE url=%s", (request.url,)
            )
            if res and res[0][0]:
                if request.meta.get("dont_refresh"):
                    spider.logger.debug("Not refreshing %s", request.url)
                    raise IgnoreRequest()
                d = res[0][0].strftime("%a, %d %b %Y %H:%M:%S %z")
                spider.logger.info(f"Setting IMS to {d}")
                request.headers["If-Modified-Since"] = d

        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        if response.status == 304:
            spider.logger.debug(f"URL {request.url} was not modified")
            raise IgnoreRequest()
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    async def _create_tables(self, cur):
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                source_id VARCHAR(32),
                url VARCHAR(255),
                modified_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT unique_doc UNIQUE(url)
            )"""
        )
        await cur.execute(
            """
            CREATE INDEX documents_idx1 ON documents (source_id, modified_at)
            """
        )

    async def ensure_table_exists(self, spider, conn):
        tried = False
        while True:
            res = await conn.runQuery(
                """
                SELECT table_name from information_schema.tables where table_schema='public' and table_name='documents'
                """
            )
            if res:
                break
            try:
                await conn.runInteraction(
                    lambda cur: ensureDeferred(self._create_tables(cur))
                )
            except Exception as ex:
                if tried:
                    spider.logger.error("Could not create the documents table: %s", ex)
                    return False
                tried = True
        return True

    async def spider_opened(self, spider):
        conn = txpostgres.Connection()
        try:
            await conn.connect(
                host=os.environ["SCRAPY_DB_HOST"],
                port=os.environ["SCRAPY_DB_PORT"],
                database=os.environ["SCRAPY_DB_NAME"],
                user=os.environ["SCRAPY_DB_USER"],
                password=os.environ["SCRAPY_DB_PASSWORD"],
            )
        except Exception as ex:
            spider.logger.error("Failed to connect to scrapy database: %s", ex)
            return

        if await self.ensure_table_exists(spider, conn):
            spider.db_conn = conn
            res = await conn.runQuery(
                "SELECT MAX(modified_at) FROM documents WHERE source_id=%s",
                (spider.source_id,),
            )
            if res:
                lm = res[0][0]
                if lm is not None:
                    spider.last_modified = lm
                    logging.info("Last modified: %s", spider.last_modified)

    @staticmethod
    def spider_closed(spider):
        if hasattr(spider, "db_conn"):
            spider.db_conn.close()
