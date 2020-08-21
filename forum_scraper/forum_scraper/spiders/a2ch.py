# -*- coding: utf-8 -*-

from collections import namedtuple
import re

import scrapy
from scrapy import Selector
from urllib.parse import urljoin, urlparse

from .. import items
from ..items import (
    ForumItem,
    ActiveTopicItem,
    ArchivedTopicItem,
    TopicCompletedItem
)
from ..loaders import ForumLoader, CommentLoader, TopicLoader
from ..utils.urlutil import forum_id_from_url
from ..utils.pipelines import DATETIME_PTTRN


class A2chSpider(scrapy.spiders.Spider):
    name = '2ch'
    allowed_domains = ['2ch.sc']

    def start_requests(self):
        bbs_table = 'http://2ch.sc/bbstable.html'
        yield scrapy.Request(bbs_table, self.parse_forum_list)

    def parse_forum_list(self, response):
        '''Parse the forum list of BBS. Then request for each forum.'''
        target_forums = ['livejupiter', 'news', 'news4vip', 'newsplus']
        for url in response.css('b ~ a::attr(href)').getall():
            if forum_id_from_url(url) in target_forums:
                yield scrapy.Request(url, self.parse_forum)

    def parse_forum(self, response):
        '''Parse a single forum of the BBS, extract metadata.
        Request for the archive list of the forum, call self.parse_archives.'''

        bl = ForumLoader(item=ForumItem(), response=response)
        # Basic identity
        bl.add_value('site', '2ch')
        bl.add_value('forum_id', response.url)
        bl.add_value('forum_url', response.url)
        bl.add_css('forum_name', 'title::text')
        # Foreign keys
        bl.add_value('hostname', response.url)
        item = bl.load_item()
        yield item

        # Scrape active topics
        actv_kwargs = {'forum_id': item['forum_id'],
                       'forum_url': item['forum_url'],
                       'thd_item_cls': ActiveTopicItem}
        yield response.follow('subback.html', self.parse_active_list,
                              cb_kwargs=actv_kwargs)

        # Scrape archived topics
        arch_kwargs = {'forum_id': item['forum_id'],
                       'forum_url': item['forum_url'],
                       'thd_item_cls': ArchivedTopicItem}
        yield response.follow('kako/', self.parse_archive_list,
                              cb_kwargs=arch_kwargs)

    def parse_active_list(self, response, **kwargs):
        '''Parse URLs for active topics.'''
        for topic_url in response.css('.trad > a::attr(href)'):
            m = re.match(r'\d+', topic_url.get())
            if m is not None:
                kwargs['topic_num'] = m.group(0)
                yield response.follow(f'dat/{m.group(0)}.dat',
                                      self.parse_topic, cb_kwargs=kwargs)

    def parse_archive_list(self, response, **kwargs):
        '''Parse URLs for active topics.'''
        xpath_selector = '//a[text()="subject.txt"]/@href'
        txt_urls = [urljoin(response.url, u)
                    for u in response.xpath(xpath_selector).getall()[::-1]
                    if u]
        kwargs['txt_urls'] = txt_urls
        yield scrapy.Request(txt_urls.pop(), self.parse_dat_list,
                             cb_kwargs=kwargs)

    def parse_dat_list(self, response, **kwargs):
        body = [r for r in response.text.split('\n') if r]
        kwargs['count'] = 0 if 'count' not in kwargs else kwargs['count']

        for row in body:
            fname = row.split('<>')[0]  # r'\d+\.dat'
            kwargs['topic_num'] = fname.split('.')[0]  # r'\d+'
            yield scrapy.Request(urljoin(kwargs["forum_url"], 'dat/') + fname,
                                 self.parse_topic, cb_kwargs=kwargs)

            kwargs['count'] += 1
            if kwargs['count'] > 1000:
                break

        if kwargs['count'] < 1000 and len(kwargs['txt_urls']) > 0:
            next_url = kwargs['txt_urls'][-1]   # note it's cast to a tuple
            kwargs['txt_urls'] = kwargs['txt_urls'][:-1]
            yield scrapy.Request(next_url, self.parse_dat_list,
                                 cb_kwargs=kwargs)

    def parse_topic(self, response, **kwargs):
        body = [r for r in response.text.split('\n')
                if r and not r.startswith('過去ログ')]
        topic_url = (f'http://{urlparse(response.url).netloc}/test/read.cgi/'
                     f'{kwargs["forum_id"]}/{kwargs["topic_num"]}/')

        tl = TopicLoader(item=kwargs['thd_item_cls'](), response=response)
        # Basic identity
        tl.add_value('site', '2ch')
        tl.add_value('topic_id', response.url)
        tl.add_value('topic_url', topic_url)
        first_row = self._decompose_row(body[0])
        tl.add_value('topic_title', first_row.title)
        # Metadata
        tl.add_value('posted_on', first_row.date)
        tl.add_value('last_comment_on',
                     [self._decompose_row(row).date for row in body[-20:]])
        tl.add_value('num_comments', str(min(len(body), 1000)))
        tl.add_value('reported_size', None)
        # Foreign keys
        tl.add_value('forum_id', kwargs['forum_id'])
        item = tl.load_item()
        yield item

        thd_item_name = kwargs['thd_item_cls'].__name__
        cmt_cls = getattr(items, thd_item_name.replace('Topic', 'Comment'))
        yield from self.parse_comments(body, item['topic_id'], topic_url,
                                       cmt_cls)

    def parse_comments(self, body, topic_id, topic_url, cmt_item_cls):
        i = 1
        for row in body:
            row = self._decompose_row(row)
            body_html = Selector(text=row.body)

            cl = CommentLoader(cmt_item_cls(), selector=body_html)
            # Basic identity
            cl.add_value('site', '2ch')
            cl.add_value('comment_id', topic_id)
            cl.add_value('comment_id', str(i))
            cl.add_value('comment_url', topic_url)
            cl.add_value('comment_url', str(i))
            # Metadata
            cl.add_value('posted_on_raw', row.date)
            cl.add_value('user_id', row.uid)
            cl.add_value('user_name', row.uname)
            cl.add_value('body', row.body)
            p_res = r'(\.{2})?/test/read.cgi/\w+/\d+/\d+/?'
            cl.add_value('reply_to', re.findall(p_res, row.body))
            cl.add_value('is_aa', False)
            p_img = r'\bhttps?://[\w/\.]+\.(?:png|gif|jpg)\b'
            cl.add_value('image_urls', re.findall(p_img, row.body))
            # Foreign keys
            cl.add_value('topic_id', topic_id)
            yield cl.load_item()
            i += 1

        yield TopicCompletedItem(comment_id=-1,
                                 topic_id=topic_id,
                                 posted_on_raw='2001/01/01(日) 00:00:00.00')

    def _decompose_row(self, row):
        if not isinstance(row, str):
            raise TypeError
        row_tuple = namedtuple('Row', ['uname', 'mail', 'body',
                                       'title', 'date', 'uid'])
        data = row.split('<>')
        date_uid = data.pop(2)
        m = re.match(DATETIME_PTTRN, date_uid)
        date = m.group(0) if m is not None else None
        m2 = re.search(r'([^: ]+)$', date_uid)
        uid = m2.group(0) if m2 is not None else None
        data = [seg.strip() if isinstance(seg, str) else ''
                for seg in data + [date, uid]]
        try:
            return row_tuple(*data)
        except Exception as e:
            raise Exception(e, data + [date_uid])
