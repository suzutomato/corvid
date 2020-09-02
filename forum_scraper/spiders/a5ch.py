# -*- coding: utf-8 -*-

import scrapy

from .. import items
from ..items import (
    ForumItem,
    ActiveTopicItem,
    ArchivedTopicItem,
    TopicCompletedItem
)
from ..loaders import ForumLoader, CommentLoader, TopicLoader
from ..utils.urlutil import forum_id_from_url


class A5chSpider(scrapy.spiders.Spider):
    name = '5ch'
    allowed_domains = ['5ch.net']

    def start_requests(self):
        bbs_table = 'https://menu.5ch.net/bbstable.html'
        yield scrapy.Request(bbs_table, self.parse_forum_list)

    def parse_forum_list(self, response):
        '''Parse the forum list of BBS. Then request for each forum.'''
        target_forums = self.settings.get('TARGET_FORUMS')
        for url in response.css('font > b ~ a::attr(href)').getall():
            # self.logger.debug(f'{forum_id_from_url(url)}, {target_forums}')
            if forum_id_from_url(url) in target_forums:
                yield scrapy.Request(url, self.parse_forum)

    def parse_forum(self, response):
        '''Parse a single forum of the BBS, extract metadata.
        Request for the archive list of the forum, call self.parse_archives.'''

        bl = ForumLoader(item=ForumItem(), response=response)
        # Basic identity
        bl.add_value('site', '5ch')
        bl.add_value('forum_id', response.url)
        bl.add_value('forum_url', response.url)
        bl.add_css('forum_name', 'title::text')
        # Foreign keys
        bl.add_value('hostname', response.url)
        item = bl.load_item()
        yield item

        # Scrape active topics
        actv_kwargs = {'forum_id': item['forum_id'],
                       'tpc_item_cls': ActiveTopicItem,
                       'css_selector': '.trad > a::attr(href)'}
        yield response.follow('subback.html', self.parse_list,
                              cb_kwargs=actv_kwargs)

        # Scrape archived topics
        arch_kwargs = {'forum_id': item['forum_id'],
                       'tpc_item_cls': ArchivedTopicItem,
                       'css_selector': '.title > a::attr(href)'}
        yield response.follow('kako/kako0000.html', self.parse_list,
                              cb_kwargs=arch_kwargs)

    def parse_list(self, response, **kwargs):
        '''Parse URLs for active topics.'''
        for topic_url in response.css(kwargs['css_selector']):
            yield response.follow(topic_url.get(), self.parse_topic,
                                  cb_kwargs=kwargs)

    def parse_topic(self, response, **kwargs):
        '''Parse and extract metadata from single topic.
        Then call self.parse_comments.
        '''
        tl = TopicLoader(item=kwargs['tpc_item_cls'](), response=response)
        # Basic identity
        tl.add_value('site', '5ch')
        tl.add_value('topic_id', response.url)
        tl.add_value('topic_url', response.url)
        tl.add_css('topic_title', 'title::text')
        # Metadata
        tl.add_css('posted_on', '#1 > .meta > .date::text')
        tl.add_css('last_comment_on', '.topic .date::text')
        stats = response.css('.pagestats .meta::text').getall()
        tl.add_value('num_comments', stats)
        tl.add_value('reported_size', stats)
        # Foreign keys
        tl.add_value('forum_id', kwargs['forum_id'])
        item = tl.load_item()
        yield item

        # Get a proper CommentItem class from matome.items
        tpc_item_name = kwargs['tpc_item_cls'].__name__
        cmt_cls = getattr(items, tpc_item_name.replace('Topic', 'Comment'))
        yield from self.parse_comments(response, item['topic_id'], cmt_cls)

    def parse_comments(self, response, topic_id, cmt_item_cls):
        for comment in response.css('div.topic > div.post'):
            cl = CommentLoader(cmt_item_cls(), selector=comment)
            # Basic identity
            cl.add_value('site', '5ch')
            cl.add_value('comment_id', topic_id)
            cl.add_css('comment_id', '.number::text')
            cl.add_value('comment_url', response.url)
            cl.add_css('comment_url', '.number::text')
            # Metadata
            cl.add_css('posted_on_raw', '.date::text')
            cl.add_css('user_id', '.uid', re=r'ID:([^<]+)<')
            cl.add_css('user_name', '.name b::text')
            cl.add_css('body', '.escaped')
            cl.add_css('reply_to', '.reply_link::attr(href)')
            cl.add_css('is_aa', '.AA')
            cl.add_css('image_urls', '.image::attr(href)')
            # Foreign keys
            cl.add_value('topic_id', topic_id)
            yield cl.load_item()

        yield TopicCompletedItem(comment_id=-1,
                                 topic_id=topic_id,
                                 posted_on_raw='2001/01/01(日) 00:00:00.00')
