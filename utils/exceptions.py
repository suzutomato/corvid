from scrapy.exceptions import IgnoreRequest


class BlacklistedURLException(IgnoreRequest):
    '''When a URL yields a status code greater than 400 and is a forum url.'''
    pass


class ExpiredURLException(IgnoreRequest):
    '''When a URL yields a status code greater than 400 and is a topic url.'''
    pass


class AlreadyScrapedURLsException(IgnoreRequest):
    '''When a URL is in the latest `scraped_urls'''
    pass
