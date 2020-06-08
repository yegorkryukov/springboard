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
    info('get_and_store_function')
    logger.info(f'==========WORKING==========> {ticker}')
    client = pm.MongoClient('mongodb://localhost:27017')
    collection = client['news']['recommendations']
    finwiz_url = 'https://finviz.com/quote.ashx?t='
    url = finwiz_url + ticker
    req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
    response = urlopen(req)    
    html = BeautifulSoup(response, 'html.parser')
    news_table = html.find(id='news-table')

    for x in news_table.findAll('tr'):

        title = x.a.get_text() 
        link = x.a['href']

        # check if this url was scraped already
        logger.info(f'Checking url: {link}')
        if collection.find_one({'news.url':link}): 
            logger.info('URL has been found, continue to the next one.')
            continue
        else:
            logger.info('URL not found. Trying to download and process article.')
        
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
            article = Article(link)
            article.download()
            article.parse()
            article.nlp()
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
        
        logger.info(f"Saved {ticker}: {dt}/ {doc['news']['title']}")
        
logging.basicConfig(level=logging.INFO)

import os

def info(title):
    logger.info(title)
    logger.info(f'module name: {__name__}')
    logger.info(f'parent process: {os.getppid()}')
    logger.info(f'process id:, {os.getpid()}')

if __name__ == '__main__': 
    
    info('Main line')
    tickers = si.tickers_sp500()
    
    p = Pool()
    result = p.map_async(get_and_store_news, tickers)
    # result.get()
    p.close()
    p.join()
    logger.info(f'Finished at {datetime.datetime.now()}')
