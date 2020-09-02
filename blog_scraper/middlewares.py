# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from corvid.utils.middlewares import BaseDownloaderMiddleware
from .items import ArticleItem


def get_key_from_url(url: str):
    if not isinstance(url, str):
        key = None

    parsed = urlparse(url)
    host = parsed.netloc.split(':')[0]

    if host == 'blog.livedoor.jp':
        key = parsed.path.strip('/').split('/')[0]

    elif not parsed.path.replace('/', ''):
        key = host.split('.')[-2]
        if key in ('livedoor', '2chblog', 'doorblog'):
            key = host.split('.')[-3]

    else:
        key = None

    return key if key else None


class BlogDownloaderMiddleware(BaseDownloaderMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_key = get_key_from_url
        self.trgt_item_cls = ArticleItem
