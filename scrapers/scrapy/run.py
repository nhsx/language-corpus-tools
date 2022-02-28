#!/usr/bin/env python3

import inspect
import os
import os.path
import glob
import importlib

import scrapy
from scrapy.crawler import CrawlerProcess
import scrapy.settings

modules = glob.glob(os.path.join('corpus', 'spiders', '*.py'))
files = [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

settings = scrapy.settings.Settings()
settings.setmodule('corpus.settings')

s = os.environ.get('SCRAPY_HTTPCACHE_ENABLED')
if s is not None:
  settings.set('HTTPCACHE_ENABLED', s, 'cmdline')


process = CrawlerProcess(settings)

for f in files:
  mod = importlib.import_module('corpus.spiders.'+f)

  for name, obj in inspect.getmembers(mod):
    if inspect.isclass(obj):
      if issubclass(obj, scrapy.Spider):
        process.crawl(obj)

process.start()

