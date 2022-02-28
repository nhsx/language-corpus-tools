import re
from typing import List
from urllib.parse import urljoin
from lxml import etree
import dateutil.parser

import scrapy

from corpus import items
from corpus.util import strip_tags

def extract_item_id(href: str) -> str:
    m = re.search(r"(?:^|\/)([^\/]+).html$", href)
    if m:
        return m.group(1)
    return ""


def clear_class(attrib: dict) -> dict:
    return {key: value for key, value in attrib.items() if key != "class"}


class TableItem:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def extract_value(selector: scrapy.selector.Selector) -> str:
        return "".join(selector.xpath(".//text()").getall()).strip()


class TableItemRef(TableItem):
    def extract_value(self, selector: scrapy.selector.Selector) -> str:
        a = selector.xpath("a")
        if a:
            return extract_item_id(a[0].attrib.get("href"))
        return None

class TableItemDescription(TableItem):
    def __init__(self, name, dict_item, doc_url):
        super().__init__(name)
        self.dict_item = dict_item
        self.doc_url = doc_url

    def extract_value(self, selector: scrapy.selector.Selector) -> str:
        if selector.root is not None:
            dst = etree.Element("article")
            self.dict_item.convert_description(selector.root, dst, self.doc_url)
            return etree.tostring(dst, method="html", encoding="utf-8").decode("utf-8")
        return super().extract_value(selector)


class TableItemBool(TableItem):
    def extract_value(self, selector: scrapy.selector.Selector) -> str:
        return (selector.xpath("text()").get() or "").strip() != ""


def extract_table(headers: List[TableItem], rows: scrapy.selector.SelectorList) -> List[str]:
    a = []
    for row in rows:
        d = {}
        for i, val in enumerate(row.xpath("td")):
            hdr = headers[i]
            d[hdr.name] = hdr.extract_value(val)
        a.append(d)
    return a


class DictionaryItem:
    __slots__ = "item_type", "item_id", "item_type_in_id", "links"

    def __init__(self, item_type, item_type_in_id=None):
        if item_type_in_id is None:
            item_type_in_id = item_type
        self.item_type = item_type
        self.item_type_in_id = item_type_in_id
        self.links = []
        self.item_id = None

    def convert_description(self, src, dst, doc_url):
        dst.text = src.text
        dst.tail = src.tail
        for child in src:
            if etree.iselement(child):
                if child.tag == "a":
                    href = child.attrib.get("href")
                    child_dst = etree.Element("a", {"href": href})
                    cls = (child.attrib.get("class") or "").split()
                    internal_link = False
                    for item_type in [
                        "element",
                        "attribute",
                        "class",
                        "businessDefinition",
                        "dataSet"
                    ]:
                        if item_type in cls:
                            item_id = extract_item_id(href)
                            child_dst.attrib["data-item-type"] = item_type
                            child_dst.attrib["data-item-id"] = item_id
                            del child_dst.attrib["href"]
                            if item_id != "" and (
                                item_id != self.item_id or item_type != self.item_type
                            ):
                                link = {"item_type": item_type, "item_id": item_id}
                                if link not in self.links:
                                    self.links.append(link)
                            internal_link = True
                            break
                    if not internal_link:
                        child_dst.attrib["href"] = urljoin(doc_url, href)
                else:
                    if child.tag == "script":
                        continue
                    else:
                        child_dst = etree.Element(child.tag, clear_class(child.attrib))
                dst.append(child_dst)
                self.convert_description(child, child_dst, doc_url)
            else:
                dst.append(child)

    def parse(self, response):
        self.item_id = response.request.meta["item_id"]
        a = response.xpath('/html/body//div[@id="wh_topic_body"]')
        if a:
            b = a[0]
            meta = {}

            fmt_len = (
                b.xpath(
                    f'//article[@id="{self.item_type_in_id}_{self.item_id}.format___length"]'
                )
                .css("div.body")
                .get()
            )
            if fmt_len:
                fmt_len = strip_tags(fmt_len).strip()
                if fmt_len:
                    meta["format"] = fmt_len


            if self.item_type == "dataSet":
                description = b.xpath(
                    f'//article[@id="{self.item_type_in_id}_{self.item_id}.overview"]'
                ).css("div.body div")[0]
            else:
                description = b.xpath(
                    f'//article[@id="{self.item_type_in_id}_{self.item_id}.description"]'
                ).css("div.body div")[0]
            dst = etree.Element("article")
            self.convert_description(description.root, dst, response.url)

            aliases = self.extract_item_table(
                b, "also_known_as", [TableItem("context"), TableItem("alias")]
            )
            if aliases:
                meta["aliases"] = aliases

            national_codes = self.extract_item_table(
                b,
                "national_codes",
                [
                    TableItem("code"),
                    TableItemDescription("description", self, response.url),
                ],
            )
            if national_codes:
                meta["national_codes"] = national_codes

            # data element specific
            attribute = b.xpath(
                f'//article[@id="{self.item_type_in_id}_{self.item_id}.attribute"]'
            ).css("a.attribute")
            if attribute:
                attribute_id = extract_item_id(attribute[0].attrib.get("href"))
                if attribute_id != "":
                    self.links.append(
                        {
                            "link_type": "element_attribute",
                            "item_type": "attribute",
                            "item_id": attribute_id,
                        }
                    )

            # class specific
            attributes = self.extract_item_table(
                b, "attributes", [TableItemBool("key"), TableItemRef("attribute")]
            )
            for attr in attributes:
                if attr["key"]:
                    link_type = "key_attribute"
                else:
                    link_type = "attribute"
                self.links.append(
                    {
                        "link_type": link_type,
                        "item_type": "attribute",
                        "item_id": attr["attribute"],
                    }
                )

            # dataset specific
            ds_spec = response.xpath(f'//article[@id="{self.item_type_in_id}_{self.item_id}.specification"]').css("div.body")
            if ds_spec:
                spec_elt = etree.Element("article")
                self.convert_description(ds_spec[0].root, spec_elt, response.url)
                meta["ds_spec"] = etree.tostring(spec_elt, method="html", encoding="utf-8").decode("utf-8")

            name = response.xpath('/html/head/meta[@name="name"]/@content').get()
            lm = response.headers.get("Last-Modified")
            if lm is not None:
                modified_at = dateutil.parser.parse(lm)
            else:
                modified_at = None

            if not meta:
                meta = None

            return items.DataDictionaryItem(
                source_url=response.url,
                modified_at=modified_at,
                item_type=self.item_type,
                item_id=self.item_id,
                name=name,
                description=etree.tostring(dst, method="html", encoding="utf-8").decode(
                    "utf-8"
                ),
                links=self.links,
                meta=meta,
            )

        return None

    def extract_item_table(self, b, attr, headers):
        return extract_table(
            headers,
            b.xpath(
                f'//article[@id="{self.item_type_in_id}_{self.item_id}.{attr}"]//table/tbody/tr'
            ),
        )


class DataDictionaryScraper(scrapy.Spider):
    name = "datadictionary"
    source_id = name
    # custom_settings = {"HTTPCACHE_POLICY": "scrapy.extensions.httpcache.RFC2616Policy"}

    def start_requests(self):
        return [
            scrapy.Request(
                "https://datadictionary.nhs.uk/data_elements_overview.html",
                self.parse_data_elements_index,
            ),
            scrapy.Request(
                "https://datadictionary.nhs.uk/attributes_overview.html",
                self.parse_attributes_index,
            ),
            scrapy.Request(
                "https://datadictionary.nhs.uk/classes_overview.html",
                self.parse_classes_index,
            ),
            scrapy.Request(
                "https://datadictionary.nhs.uk/nhs_business_definitions_overview.html",
                self.parse_business_def_index,
            ),
            scrapy.Request(
                "https://datadictionary.nhs.uk/data_sets_overview.html",
                self.parse_dataset_index,
            ),
        ]

    def parse_data_elements_index(self, response):
        for item in response.xpath(
            '/html/body//article[@id="dataElement_overview"]/article'
        ).css("a.element"):
            href = item.attrib.get("href")
            m = re.search(r"data_elements\/([^\/]+).html$", href)
            if m:
                item_id = m.group(1)
            else:
                self.logger.warn(f"Could not extract id from {href}")
                continue
            # self.logger.debug(f"Extracted {href}")
            yield response.follow(
                href, self.parse_data_element, meta={"item_id": item_id}
            )
            # return

    def parse_attributes_index(self, response):
        for item in response.xpath(
            '/html/body//article[@id="attribute_overview"]/article'
        ).css("a.attribute"):
            href = item.attrib.get("href")
            m = re.search(r"attributes\/([^\/]+).html$", href)
            if m:
                item_id = m.group(1)
            else:
                self.logger.warn(f"Could not extract id from {href}")
                continue
            # self.logger.debug(f"Extracted {href}")
            yield response.follow(href, self.parse_attribute, meta={"item_id": item_id})
            # return

    def parse_classes_index(self, response):
        for item in response.xpath(
            '/html/body//article[@id="class_overview"]/article'
        ).css("a.class"):
            href = item.attrib.get("href")
            m = re.search(r"classes\/([^\/]+).html$", href)
            if m:
                item_id = m.group(1)
            else:
                self.logger.warn(f"Could not extract id from {href}")
                continue
            # self.logger.debug(f"Extracted {href}")
            yield response.follow(href, self.parse_class, meta={"item_id": item_id})
            # return

    def parse_business_def_index(self, response):
        for item in response.xpath(
            '/html/body//article[@id="business_definitions_overview"]/article'
        ).css("a.businessDefinition"):
            href = item.attrib.get("href")
            m = re.search(r"nhs_business_definitions\/([^\/]+).html$", href)
            if m:
                item_id = m.group(1)
            else:
                self.logger.warn(f"Could not extract id from {href}")
                continue
            # self.logger.debug(f"Extracted {href}")
            yield response.follow(
                href, self.parse_business_def, meta={"item_id": item_id}
            )
            # return

    def parse_dataset_index(self, response):
        for item in response.xpath(
            '/html/body//ul[@role="tree"]//span[@data-state="leaf"]').css("span.title a"):
            href = item.attrib.get("href")
            m = re.search(r"\/([^\/]+).html#", href)
            if m:
                item_id = m.group(1)
            else:
                self.logger.warn(f"Could not extract id from {href}")
                continue
            # self.logger.debug(f"Extracted {href}")
            yield response.follow(
                href, self.parse_dataset, meta={"item_id": item_id}
            )
            # return

        for item in response.xpath(
            '/html/body//ul[@role="tree"]//span[@data-state="not-ready"]').css("span.title a"):
            a_id = item.attrib.get("id") or ""
            if a_id.startswith("data_sets."):
                yield response.follow(item.attrib.get("href"), self.parse_dataset_index)

    def parse_data_element(self, response):
        return self.parse_dict_item(response, "element")

    def parse_attribute(self, response):
        return self.parse_dict_item(response, "attribute")

    def parse_class(self, response):
        return self.parse_dict_item(response, "class")

    def parse_business_def(self, response):
        return self.parse_dict_item(
            response, "businessDefinition", "business_definition"
        )

    def parse_dataset(self, response):
        return self.parse_dict_item(
            response, "dataSet", "dataset"
        )

    @staticmethod
    def parse_dict_item(response, typ, typ_in_id=None):
        dict_item = DictionaryItem(typ, typ_in_id)
        item = dict_item.parse(response)
        if item is not None:
            yield item
