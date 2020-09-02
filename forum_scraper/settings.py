# -*- coding: utf-8 -*-

from pathlib import Path
import sys

parent_dir = str(Path(__file__).resolve().parents[2])
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Scrapy settings for forum_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'forum_scraper'

SPIDER_MODULES = ['forum_scraper.spiders']
NEWSPIDER_MODULE = 'forum_scraper.spiders'

'''
# Crawl responsibly by identifying yourself (and your website) on the
# user-agent
#USER_AGENT = 'forum_scraper (+http://www.yourdomain.com)'
'''
# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0.5

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': None,
    'forum_scraper.middlewares.ForumDownloaderMiddleware': 543,
}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'scrapy.pipelines.images.ImagesPipeline': 1,
    'forum_scraper.pipelines.DatetimePipeline': 300,
    'forum_scraper.pipelines.ForumItemExportPipeline': 700,
    'forum_scraper.pipelines.TopicItemExportPipeline': 710,
    'forum_scraper.pipelines.CommentItemExportPipeline': 720
}
