# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from collections import defaultdict
import csv
import logging
from pathlib import Path
from urllib.parse import urlparse

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from corvid.forum_scraper.utils import urlutil as uu
from corvid.utils.classes import ItemBuffer
from .items import ArticleItem


class ArticleItemPipeline:
    logger = logging.getLogger('pipelines.ArticleItemPipeline')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.art_buffer = defaultdict(ItemBuffer)
        self.logger.debug('initiated')

    @classmethod
    def from_crawler(cls, crawler):
        kwargs = {
            'daily_dir_path': Path(crawler.settings.get('DAILY_DIR')),
            'filename_tmplt': crawler.settings.get('BLOG_TEMPLATE')
        }
        return cls(**kwargs)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        blog_name = adapter['blog']  # Raise if not exist

        if isinstance(item, ArticleItem):
            if not adapter['src_url']:
                raise DropItem(f'no `src_url` found: {adapter["art_url"]}')
            if 'https://girlschannel.net/topics' in adapter['src_url'][-1]:
                raise DropItem(
                    f'girlschannel found: {item["art_url"]} - '
                    f'{adapter["src_url"][-1]}'
                )
            if not adapter['cmt_ids']:
                raise DropItem(f'no comment found: {adapter["art_url"]}')

            adapter['src_url'] = src_url = adapter['src_url'][-1]
            adapter['src_site'] = urlparse(src_url).netloc.split('.')[-2]
            adapter['topic_id'] = topic_id = uu.topic_id_from_url(src_url)
            adapter['cmt_ids'] = [f'{topic_id}_{int(cmt):0>4}'
                                  for cmt in adapter['cmt_ids']]

            self.art_buffer[blog_name].store(item)

            # Log
            count = len(self.art_buffer[blog_name]) - 1
            self.logger.debug(f'added an item for {blog_name}: total {count}')

        return item

    def close_spider(self, spider):

        for blog_name, buffer in self.art_buffer.items():

            file_name = self.filename_tmplt.format(blog=blog_name)
            path = self.daily_dir_path / file_name

            with path.open('w') as wh:
                writer = csv.writer(wh)
                for row in buffer:
                    writer.writerow(row)

            # Log
            self.logger.debug(
                f'Exported {len(buffer)-1} items for {blog_name}'
            )

        return None
