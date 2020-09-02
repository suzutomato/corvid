# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from collections import defaultdict
import logging
from pathlib import Path

from scrapy import signals

from .items import ArchivedTopicItem
from .utils.classes import URLOrderedSet
from .utils.exceptions import (
    BlacklistedURLException,
    ExpiredURLException,
    AlreadyScrapedURLsException
)
from .utils.fileutil import read_pickle, to_pickle
from .utils.urlutil import (
    forum_id_from_url,
    is_forum_url,
    is_topic_url
)

logger = logging.getLogger(__name__)


class DownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def __init__(self, latest_dir_pointer, daily_dir):
        self.latest_dir_pointer = Path(latest_dir_pointer)
        self.daily_dir = Path(daily_dir)

        try:
            with open(latest_dir_pointer) as rh:
                latest_dir = Path(next(rh))
        except Exception:
            latest_dir = ''

        if latest_dir:
            latest_dir = Path(latest_dir)
            self.blacklist = read_pickle(latest_dir/'blacklist.pickle', set())
            self.scraped_urls = read_pickle(latest_dir/'scraped_urls.pickle',
                                            defaultdict(URLOrderedSet))
            self.expired_urls = read_pickle(latest_dir/'expired_urls.pickle',
                                            defaultdict(URLOrderedSet))
        else:
            self.blacklist = set()
            self.scraped_urls = defaultdict(URLOrderedSet)
            self.expired_urls = defaultdict(URLOrderedSet)

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        latest_dir_pointer = settings.get('LATEST_DIR_POINTER')
        daily_dir = settings.get('DAILY_DIR')

        s = cls(latest_dir_pointer, daily_dir)
        crawler.signals.connect(s.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        if request.url in self.blacklist:
            logger.debug(f'Request ignored: blacklist: {request.url}')
            raise BlacklistedURLException()

        forum_id = forum_id_from_url(request.url)
        if request.url in self.expired_urls.get(forum_id, []):
            logger.debug(f'Request ignored: known expired: {request.url}')
            raise ExpiredURLException()

        if request.url in self.scraped_urls.get(forum_id, []):
            logger.debug(f'Request ignored: previously scraped: {request.url}')
            raise AlreadyScrapedURLsException()

        return None

    def process_response(self, request, response, spider):
        if 400 <= response.status < 500:
            if is_forum_url(request.url):
                self.blacklist.add(request.url)
                logger.warning(
                    f'Response ignored: status {response.status} '
                    f'({request.url}), added to blacklist.'
                )
                raise BlacklistedURLException()

            elif is_topic_url(request.url):
                forum_id = forum_id_from_url(request.url)
                self.expired_urls[forum_id].add_url(request.url)
                logger.warning(
                    f'Response ignored: status {response.status} '
                    f'({request.url}), added to expired_urls list.'
                )
                raise ExpiredURLException()

        return response

    def process_exception(self, request, exception, spider):
        return None

    def item_scraped(self, item, response, spider):
        if isinstance(item, ArchivedTopicItem):
            forum_id = forum_id_from_url(response.url)
            if forum_id is not None:
                self.scraped_urls[forum_id].add_url(response.url)
        return None

    def spider_closed(self, spider, reason):
        import sys
        sys.setrecursionlimit(10000)

        for uos in self.scraped_urls.values():
            uos.trim()
            uos.set_pivot_url()

        for uos in self.expired_urls.values():
            uos.trim()
            uos.set_pivot_url()

        to_pickle(self.blacklist, self.daily_dir/'blacklist.pickle')
        to_pickle(self.scraped_urls, self.daily_dir/'scraped_urls.pickle')
        to_pickle(self.expired_urls, self.daily_dir/'expired_urls.pickle')

        with open(self.latest_dir_pointer, 'w') as wh:
            wh.write(str(self.daily_dir))
