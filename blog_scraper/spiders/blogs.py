# -*- coding: utf-8 -*-
import os
from pathlib import Path
import pickle
import re
from typing import Optional
from urllib.parse import urlparse

import scrapy

from ..items import ArticleItem


class BlogInfo:
    def __init__(self, url: str, name: str,
                 art_sel: str, cmt_sel: str, src_sel: str,
                 pp_sel: str = 'p={}',
                 first_page: int = 1,
                 art_regex: Optional[str] = None,
                 cmt_regex: Optional[str] = None,
                 src_regex: Optional[str] = None):
        self.url = url
        self.name = name
        self.pp_sel = pp_sel
        self.art_sel = art_sel
        self.cmt_sel = cmt_sel
        self.src_sel = src_sel
        self.first_page = first_page

        URL_PAT = r'(https?://[\w\$\-\.\+\!\*\'\?\:\(\)_,;/@=&#]+)'
        FORUM_URL_PAT = r'(https?://\w+\.(?:2ch|5ch|open2ch)\.\w+/' + \
                        r'[\w\$\-\.\+\!\*\'\?\:\(\)_,;/@=&#]+)'
        COMMENT_PAT = r'(\d+)'
        self.art_regex = URL_PAT if art_regex is None else art_regex
        self.cmt_regex = COMMENT_PAT if cmt_regex is None else cmt_regex
        self.src_regex = FORUM_URL_PAT if src_regex is None else src_regex


class BlogsSpider(scrapy.Spider):
    name = 'blogs'
    FORUM_DOMAINS = {'2ch.sc', '5ch.net', 'open2ch.net'}

    def start_requests(self):
        config_dir = Path(os.environ['SCRAPER_CONFIG_DIR'])

        with (config_dir/'blogs.pickle').open('rb') as rh:
            blog_params = self.get_blog_info(pickle.load(rh))

        for blog_param in blog_params:
            yield scrapy.Request(blog_param.url, self.parse,
                                 cb_kwargs=dict(blog_param=blog_param))

    def parse(self, response, **cb_kwargs):
        bp = cb_kwargs['blog_param']  # Blog named-tuple
        art_urls = cb_kwargs.get('art_urls', set())  # Article URLs
        curr_page = cb_kwargs.get('curr_page', bp.first_page)  # Current page

        # Move to the next step when article URLs is more than `max_articles`
        # or it has scraped more pages than `max_pages`.
        max_articles = 10
        max_pages = 2
        if len(art_urls) >= max_articles or curr_page >= max_pages:
            for art_url in art_urls:
                yield scrapy.Request(art_url, self.parse_article,
                                     cb_kwargs=cb_kwargs)

        # If not enough article urls, scrape more
        else:
            urls = self.select(response, bp.art_sel, bp.art_regex)

            for url in urls:
                if url.startswith(bp.url):
                    self.logger.debug(f'scraped article url: {url}')
                    art_urls.add(url)

            # Go to next page
            curr_page += 1
            url = bp.url + '?' + bp.pp_sel.format(curr_page)
            kwargs = {
                'blog_param': bp,
                'art_urls': art_urls,
                'curr_page': curr_page
            }
            yield scrapy.Request(url, self.parse, cb_kwargs=kwargs)

    def parse_article(self, response, **cb_kwargs):
        bp = cb_kwargs['blog_param']

        # Extract source URL
        m = self.select(response, bp.src_sel, bp.src_regex)
        if m:
            srcs = [u for u in m
                    if '.'.join(urlparse(u).netloc.split('.')[-2:])
                    in self.FORUM_DOMAINS]
        else:
            srcs = []
        if not srcs:
            gc_pat = r'(https?://girlschannel.net/topics/\d+/)'
            srcs = self.select(response, bp.src_sel, gc_pat)
        # Extract comment IDs
        comments = [*set(self.select(response, bp.cmt_sel, bp.cmt_regex))]

        result = ArticleItem(blog=bp.name, art_url=response.url,
                             src_url=srcs, src_site=None,
                             cmt_ids=comments, topic_id=None)

        return result

    def select(self, response, selector, regex):

        if selector is not None and not isinstance(selector, str):
            raise ValueError('`selector` is provided but not str')
        if not isinstance(regex, str):
            raise ValueError('`regex` is not str')

        if selector is None:
            body = response.body.decode(response.encoding)
            res = re.findall(regex, body)
        else:
            if '/' in selector:
                res_html = response.xpath(selector)
            else:
                res_html = response.css(selector)
            res = [re.search(regex, r).group(1) for r in res_html.getall()
                   if re.search(regex, r)]
        return res

    def get_blog_info(self, blog_list):
        return [BlogInfo(**kwargs) for kwargs in blog_list]
