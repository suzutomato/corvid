# -*- coding: utf-8 -*-

# Define models for scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


# Forum Items
class BaseForumItem(scrapy.Item):
    '''Item object to store information of BBS on 5ch website.'''
    # Basic identity
    site = scrapy.Field()
    forum_id = scrapy.Field()
    forum_url = scrapy.Field()
    forum_name = scrapy.Field()

    # Foreign keys
    hostname = scrapy.Field()


class ForumItem(BaseForumItem):
    pass


# TopicItems
class BaseTopicItem(scrapy.Item):
    '''Item object to store information of topics on BBS.'''
    # Basic identity
    site = scrapy.Field()
    topic_id = scrapy.Field()
    topic_url = scrapy.Field()
    topic_title = scrapy.Field()

    # Metadata
    posted_on = scrapy.Field()
    last_comment_on = scrapy.Field()
    is_archived = scrapy.Field()
    scraped_on = scrapy.Field()
    num_comments = scrapy.Field()
    reported_size = scrapy.Field()

    # Forign keys
    forum_id = scrapy.Field()


class ActiveTopicItem(BaseTopicItem):
    '''Item object to store information of active topics on BBS.'''
    is_archived = False
    pass


class ArchivedTopicItem(BaseTopicItem):
    '''Item object to store information of archived topics on BBS.'''
    is_archived = True
    pass


# CommentItems
class BaseCommentItem(scrapy.Item):
    '''Item object to store information of comments on topics.'''
    # Basic identity
    site = scrapy.Field()
    comment_id = scrapy.Field()
    comment_url = scrapy.Field()
    # Comment specific url is not useful
    # Comment has no title/name

    # Metadata
    posted_on = scrapy.Field()
    posted_on_raw = scrapy.Field()
    user_id = scrapy.Field()  # of the poster
    user_name = scrapy.Field()
    body = scrapy.Field()
    reply_to = scrapy.Field()
    is_aa = scrapy.Field()  # Is Ascii Art?
    image_urls = scrapy.Field()
    images = scrapy.Field()

    # Foreign keys
    topic_id = scrapy.Field()


class ActiveCommentItem(BaseCommentItem):
    '''Item object to store information of comments on active topics.'''
    pass


class ArchivedCommentItem(BaseCommentItem):
    '''Item object to store information of comments on archived topics.'''
    pass


class TopicCompletedItem(BaseCommentItem):
    pass
