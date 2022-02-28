# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
import logging
import datetime
import json
import tempfile

from txpostgres import txpostgres
from twisted.internet import reactor
from twisted.internet.defer import ensureDeferred
import twisted.web._newclient
import treq
from psycopg2.extras import Json

from scrapy.exceptions import DropItem
from scrapy import signals

from corpus import items
from corpus.util import strip_tags


class CorpusPipeline:

    enable_medcat_trainer = os.environ.get("ENABLE_MEDCAT_TRAINER", "") == "True"
    brat_data_path = os.environ.get("BRAT_DATA_PATH")

    @classmethod
    def from_crawler(cls, crawler):
        p = cls(crawler)
        crawler.signals.connect(p.engine_started, signal=signals.engine_started)

        return p

    @classmethod
    def get_medcat_dataset_id(cls, spider):
        return spider.medcat_dataset_id

    @classmethod
    def get_doccano_project_id(cls, spider):
        return spider.doccano_project_id

    def __init__(self, cralwer):
        self.crawler = cralwer
        self.db_conn = None
        self.medcat_token = None
        self.db_conn_data_dict = None

    async def connect_to_doccano(self):
        conn = txpostgres.Connection()
        try:
            await conn.connect(
                host=os.environ["DOCCANO_DB_HOST"],
                port=os.environ["DOCCANO_DB_PORT"],
                database=os.environ["DOCCANO_DB_NAME"],
                user=os.environ["DOCCANO_DB_USER"],
                password=os.environ["DOCCANO_DB_PASSWORD"],
            )
        except Exception as ex:
            logging.error("Could not connect to doccano: %s", ex)
            return None
        return conn

    async def connect_to_datadict(self):
        conn = txpostgres.Connection()
        try:
            await conn.connect(
                host=os.environ["DATADICT_DB_HOST"],
                port=os.environ["DATADICT_DB_PORT"],
                database=os.environ["DATADICT_DB_NAME"],
                user=os.environ["DATADICT_DB_USER"],
                password=os.environ["DATADICT_DB_PASSWORD"],
            )
        except Exception as ex:
            logging.error("Could not connect to datadict: %s", ex)
            return None
        return conn

    async def connect_to_medcat(self):
        try:
            resp = await treq.post(
                os.environ["MEDCAT_API_URL"] + "/api/api-token-auth/",
                json={
                    "username": os.environ["MEDCAT_USERNAME"],
                    "password": os.environ["MEDCAT_PASSWORD"],
                },
            )
        except Exception as ex:
            logging.error("Could not connect to medcat: %s", ex)
            return None

        if resp.code != 200:
            logging.error("Could not login to medcat: %s", resp.code)
            return None
        j = await resp.json()
        return j["token"]

    async def engine_started(self):
        d = self.connect_to_doccano()
        if self.enable_medcat_trainer:
            d1 = self.connect_to_medcat()
        d2 = self.connect_to_datadict()

        self.db_conn = await d
        if self.enable_medcat_trainer:
            self.medcat_token = await d1
        self.db_conn_data_dict = await d2

        if self.db_conn is None or self.enable_medcat_trainer and self.medcat_token is None or self.db_conn_data_dict is None:
            # await self.crawler.stop() -- can't do that because the engine is not marked as running at this point
            reactor.callLater(0, self.crawler.stop)

    async def insert_into_medcat(self, item, spider):
        retries = 3
        while True:
            try:
                resp = await treq.post(
                    os.environ["MEDCAT_API_URL"] + "/api/documents/",
                    json={
                        "name": item.get("source_url")[-150:],
                        "text": item.get("text"),
                        "dataset": self.get_medcat_dataset_id(spider),
                    },
                    headers={"Authorization": f"Token {self.medcat_token}"},
                )
                break
            except twisted.web._newclient.RequestTransmissionFailed as ex:
                retries -= 1
                if retries <= 0:
                    raise ex

        if resp.code != 201 and resp.code != 200:
            cnt = await resp.text()
            raise Exception(
                f"Could not create a medcat document, status: {resp.code}, resp: {cnt}"
            )

    def insert_into_brat(self, item, spider):
        if self.brat_data_path is not None:
            ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            fname = None
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix=f"{spider.source_id}_{ts}_", dir=self.brat_data_path, delete=False) as f:
                f.write(item.get("text"))
                fname = f.name
            ann_name = fname[:-3]+"ann"
            with open(ann_name, "w") as f:
                pass
            os.chmod(ann_name, 0o666)
            os.chmod(fname, 0o666)

    async def process_corpus_item(self, item, spider):
        if isinstance(item, items.HTMLItem):
            item = items.TextItem(
                text=strip_tags(item.get("html")),
                **{key: value for key, value in item.items() if key != "html"},
            )

        if self.enable_medcat_trainer:
            await self.insert_into_medcat(item, spider)

        self.insert_into_brat(item, spider)

        meta = {"source_id": spider.source_id, "source_url": item.get("source_url")}
        try:
            now = datetime.datetime.now()
            await self.db_conn.runOperation(
                """
                  INSERT INTO api_document (text, meta, created_at, updated_at, project_id, filename) VALUES (%s, %s, %s, %s, %s, %s)
                  """,
                (
                    item.get("text"),
                    json.dumps(meta),
                    now,
                    now,
                    self.get_doccano_project_id(spider),
                    "spidered",
                ),
            )
        except Exception as ex:
            spider.logger.error("Failed to insert into doccano: %s", ex)

    async def insert_dictionary_item(self, cur, item, spider):
        await cur.execute(
            """
        INSERT INTO dictionary_item (item_type, item_id, name, description, meta) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (item_type, item_id) DO
          UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, meta = EXCLUDED.meta
        """,
            (
                item["item_type"],
                item["item_id"],
                item["name"],
                item["description"],
                Json(item.get("meta")),
            ),
        )
        await cur.execute(
            """
        DELETE from link WHERE src_item_type = %s AND src_item_id = %s
        """,
            (item["item_type"], item["item_id"]),
        )
        links = item.get("links")
        if links is not None:
            for link in links:
                await cur.execute(
                    """
          INSERT INTO link (link_type, src_item_type, src_item_id, dst_item_type, dst_item_id) VALUES (%s, %s, %s, %s, %s)
          """,
                    (
                        link.get("link_type"),
                        item["item_type"],
                        item["item_id"],
                        link["item_type"],
                        link["item_id"],
                    ),
                )

    async def process_dictionary_item(self, item, spider):
        #spider.logger.debug(f"Received data dictionary item: {item}")
        await self.db_conn_data_dict.runInteraction(
            lambda cur: ensureDeferred(self.insert_dictionary_item(cur, item, spider))
        )

    async def _insert(self, cur, item, spider):
        modified_at = item.get("modified_at")
        if modified_at is not None:
            await cur.execute(
                """
                INSERT INTO documents (source_id, url, modified_at) VALUES (%s, %s, %s)
                ON CONFLICT (url) DO
                    UPDATE SET source_id = EXCLUDED.source_id, modified_at = EXCLUDED.modified_at WHERE documents.modified_at <> EXCLUDED.modified_at""",
                (spider.source_id, item.get("source_url"), modified_at),
            )
        else:
            await cur.execute("INSERT INTO documents (source_id, url) VALUES (%s, %s) ON CONFLICT (url) DO NOTHING",
                (spider.source_id, item.get("source_url")))
        if cur.rowcount == 0:
            raise DropItem()
        if isinstance(item, items.CorpusItem):
            await self.process_corpus_item(item, spider)
        elif isinstance(item, items.DataDictionaryItem):
            await self.process_dictionary_item(item, spider)

    async def process_item(self, item, spider):
        if not isinstance(item, items.BaseItem):
            return item
        if self.db_conn is None or self.enable_medcat_trainer and self.medcat_token is None:
            self.crawler.engine.close_spider(spider)
            raise DropItem()
        if item.get("source_url") is None:
            raise DropItem("Missing source_url")
        await spider.db_conn.runInteraction(
            lambda cur: ensureDeferred(self._insert(cur, item, spider))
        )
        return item
