# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArticleItem(scrapy.Item):
    blog = scrapy.Field()
    art_url = scrapy.Field()
    src_url = scrapy.Field()
    src_site = scrapy.Field()
    topic_id = scrapy.Field()
    cmt_ids = scrapy.Field()


class BlogCompletedItem(scrapy.Item):
    '''Is used and work as a notification when spider completes scraping a
    blogs, so that pipeline can export a csv file.
    '''
    blog = scrapy.Field()
