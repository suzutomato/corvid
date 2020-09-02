# -*- coding: utf-8 -*-

from collections import defaultdict
import logging
from pathlib import Path

from scrapy import signals

from .fileutil import read_pickle, to_pickle
from .classes import URLOrderedSet
from .exceptions import (
    BlacklistedURLException,
    ExpiredURLException,
    AlreadyScrapedURLsException
)


class BaseDownloaderMiddleware:

    def __init__(self, latest_dir_pointer, daily_dir):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.latest_dir_pointer = Path(latest_dir_pointer)
        self.daily_dir = Path(daily_dir)

        # Read `latest_dir_pointer`.
        # the pointer contains the path to latest.txt in the latest daily dir,
        # which contains the paths to expired_urls, scraped_urls and blacklist.
        try:
            with latest_dir_pointer.open() as rh:
                latest_dir = Path(next(rh))
            bl_path = latest_dir / 'blacklist.pickle'
            su_path = latest_dir / 'scraped_urls.pickle'
            eu_path = latest_dir / 'expired_urls.pickle'
        except Exception:
            # If there is a problem opening/reading the path, ignore history,
            # scrape all and regenerate expired_urls, scraped_urls, blacklist.
            bl_path = su_path = eu_path = None

        # blacklist of URLs to skip.
        self.blacklist = read_pickle(bl_path, set())

        # The following two attributes are dicts of sets of URLs to skip.
        # Their key must be retrievable from URLs with `self.get_key` method.

        # URLs already scraped before. Updated whenever an instance of
        # `self.trgt_item_cls` is scraped.
        self.scraped_urls = read_pickle(su_path, defaultdict(URLOrderedSet))

        # URLs that are expired (returned status greater than 400).
        self.expired_urls = read_pickle(eu_path, defaultdict(URLOrderedSet))

        # A function to get keys of `self.expired_urls` and `self.scraped_urls`
        # Assign on the actual middleware
        self.get_key = None

        # Item class(es) for which to update `self.scraped_urls` whenever an
        # instance of them is scraped.
        # Assign on the actual middleware
        self.trgt_item_cls = None

    @classmethod
    def from_crawler(cls, crawler):
        '''Read relevant configurations from settings, hook signals to methods
        and return a Midleware instance'''

        # Read settings and initiate an instance.
        settings = crawler.settings
        latest_dir_pointer = settings.get('LATEST_DIR_POINTER')
        daily_dir = settings.get('DAILY_DIR')
        s = cls(latest_dir_pointer, daily_dir)

        # Connect signals to methods.
        crawler.signals.connect(s.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)

        return s

    def process_request(self, request, spider):
        if request.url in self.blacklist:
            self.logger.debug(f'Request ignored: blacklisted: {request.url}')
            raise BlacklistedURLException()

        key = self.get_key(request.url)
        if request.url in self.expired_urls.get(key, []):
            self.logger.debug(f'Request ignored: has expired: {request.url}')
            raise ExpiredURLException()

        if request.url in self.scraped_urls.get(key, []):
            self.logger.debug(
                f'Request ignored: already scraped: {request.url}'
            )
            raise AlreadyScrapedURLsException()

    def process_response(self, request, response, spider):
        if 400 <= response.status:
            key = self.get_key(request.url)
            if key is not None:
                self.expired_urls[key].add_url(request.url)
                self.logger.warning(
                    f'Response ignored: status {response.status} '
                    f'({request.url}), added to expired_urls list.'
                )
                raise ExpiredURLException()

        return response

    def item_scraped(self, item, response, spider):
        if isinstance(item, self.trgt_item_cls):
            key = self.get_key(response.url)
            if key is not None:
                self.scraped_urls[key].add_url(response.url)
        return None

    def spider_closed(self, spider, reason):
        # TODO: minimize recursion with URLOrderedSet
        import sys
        sys.setrecursionlimit(10000)

        for uos in self.scraped_urls.values():  # uos = URL Ordered Set
            uos.trim()
            uos.set_pivot_url()

        for uos in self.expired_urls.values():
            uos.trim()
            uos.set_pivot_url()

        to_pickle(self.blacklist, self.daily_dir/'blacklist.pickle')
        to_pickle(self.scraped_urls, self.daily_dir/'scraped_urls.pickle')
        to_pickle(self.expired_urls, self.daily_dir/'expired_urls.pickle')

        with self.latest_dir_pointer.open('w') as wh:
            wh.write(str(self.daily_dir.resolve()))  # Write abs path
