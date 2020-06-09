import pymongo as pm
import requests
from multiprocessing import Pool
import logging
from yahoo_fin import stock_info as si 
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from datetime import datetime
from datetime import date

logger = logging.getLogger(__name__)

def get_and_store_news(ticker):
    """
    Obtaines news for the 'ticker' and save to MongoDB
    """
    logger.info(f'==========WORKING==========> {ticker}')
    client = pm.MongoClient('mongodb://localhost:27017')
    collection = client['news']['recommendations']
    finwiz_url = 'https://finviz.com/quote.ashx?t='
    url = finwiz_url + ticker
    req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
    response = urlopen(req)    
    html = BeautifulSoup(response, 'html.parser')
    news_table = html.find(id='news-table')

    saved_news_counter = 0

    for x in news_table.findAll('tr'):

        title = x.a.get_text() 
        link = x.a['href']

        # check if this url was scraped already
        logger.debug(f'Checking url: {link}')
        if collection.find_one({'news.url':link}): 
            logger.debug('URL has been found, continue to the next one.')
            continue
        else:
            logger.debug('URL not found. Trying to download and process article.')
        
        date_scrape = x.td.text.strip().split()

        if len(date_scrape) == 1:
            time = date_scrape[0]
            
        else:
            date = date_scrape[0]
            time = date_scrape[1]
        
        try:
            dt = date + ' ' + time
        except:
            dt = 'NaN'

        try:
            logger.debug(f'Downloading and processing {link}')
            article = Article(link)
            article.download()
            article.parse()
            article.nlp()
            logger.debug(f'Downloaded {article.title} | {link}')
        except:
            continue
        
        doc = {
            'news' : {
                'datetime' : dt,
                'url'      : link,
                'title'    : title,
                'text'     : article.text,
                'keywords' : article.keywords,
                'summary'  : article.summary
            }
        }

        collection.update_one(
            {'ticker' : ticker},
            {'$addToSet': doc},
            upsert = True
        )

        saved_news_counter += 1
        
        logger.debug(f"Saved {ticker}: {dt}/ {doc['news']['title']}")
    
    logger.info(f'{ticker}: scraped and saved {saved_news_counter} new articles')

    # return saved_news_counter
        
logging.basicConfig(level=logging.INFO)

import os

# def info(title):
#     logger.info(title)
#     logger.info(f'module name: {__name__}')
#     logger.info(f'parent process: {os.getppid()}')
#     logger.info(f'process id:, {os.getpid()}')

if __name__ == '__main__': 
    
    logger.info(f'Starting news collector at {datetime.now()}')
    tickers = si.tickers_sp500()
    # tickers= ['AAPL','MSFT']
    
    p = Pool()
    result = p.map_async(get_and_store_news, tickers)
    p.close()
    p.join()
    logger.info(f'Finished at {datetime.now()}')