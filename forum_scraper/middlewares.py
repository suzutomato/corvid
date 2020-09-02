# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from corvid.utils.middlewares import BaseDownloaderMiddleware
from .items import ArchivedTopicItem
from .utils.urlutil import forum_id_from_url


class ForumDownloaderMiddleware(BaseDownloaderMiddleware):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_key = forum_id_from_url
        self.trgt_item_cls = ArchivedTopicItem
