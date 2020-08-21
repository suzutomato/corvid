# -*- coding: utf-8 -*-
import argparse
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import sys

from scrapy.crawler import Crawler, CrawlerProcess
from scrapy.utils.project import get_project_settings


def crawl(spider, settings):
    global runner
    crawler = Crawler(spider, settings)
    runner.crawl(crawler)


def generate_settings(site_name, base_dir, base_settings, date_dir_name):
    settings = deepcopy(base_settings)

    site_dir = base_dir / site_name
    latest_dir = site_dir / 'LATEST'
    daily_dir = site_dir / date_dir_name

    if not latest_dir.exists():
        latest_dir.mkdir(parents=True)
    if not daily_dir.exists():
        daily_dir.mkdir()

    settings['IMAGES_STORE'] = str(base_dir/'images')
    settings['LATEST_DIR_POINTER'] = str(latest_dir/'latest.txt')
    settings['DAILY_DIR'] = str(daily_dir)
    settings['DATA_DIR'] = str(daily_dir/'data')
    settings['LOG_FILE'] = str(daily_dir/'log.txt')

    return settings


if __name__ == '__main__':
    src_path = str(Path(__file__).parents[1].resolve())
    sys.path.insert(0, src_path)

    from forum_scraper.spiders.a2ch import A2chSpider
    from forum_scraper.spiders.a5ch import A5chSpider

    spider_mapping = {
        '2ch': A2chSpider,
        '5ch': A5chSpider
    }

    parser = argparse.ArgumentParser(description='Parse 2ch.sc and 5ch.net.')
    parser.add_argument('-d', default='.', type=str, required=False,
                        dest='base_dir',
                        help='Base directory for files generated by spiders')
    parser.add_argument('-t', type=str, required=True, dest='start_time',
                        help='When the task is started, used for folder names')
    parser.add_argument('-s', type=str, required=True, dest='spider',
                        help='Spider name')
    args = parser.parse_args()
    spider = args.spider
    date_dir = args.start_time
    base_dir = Path(parser.parse_args().base_dir)

    start_time = datetime.now()
    base_settings = get_project_settings()

    settings = generate_settings(spider, base_dir, base_settings, date_dir)
    process = CrawlerProcess(settings)
    process.crawl(spider_mapping[spider])
    process.start()