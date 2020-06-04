import pymongo as pm
import requests
from multiprocessing import Pool
import logging
from yahoo_fin import stock_info as si 
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request

logger = logging.getLogger(__name__)

def get_and_store_news(ticker):
    """
    Obtaines news for the 'ticker' and save to MongoDB
    """
    logger.info(f'Working on {ticker}')
    client = pm.MongoClient('mongodb://localhost:27017')
    collection = client['news']['recommendations']
    finwiz_url = 'https://finviz.com/quote.ashx?t='
    url = finwiz_url + ticker
    req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
    response = urlopen(req)    
    html = BeautifulSoup(response)
    news_table = html.find(id='news-table')

    for x in news_table.findAll('tr'):

        title = x.a.get_text() 
        link = x.a['href']
        
        date_scrape = x.td.text.strip().split()

        if len(date_scrape) == 1:
            time = date_scrape[0]
            
        else:
            date = date_scrape[0]
            time = date_scrape[1]
        dt = date + ' ' + time
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
        
        print(f"Saved {ticker}: {dt}/ {doc['news']['title']}")
        


if __name__ == '__main__': 
    logging.basicConfig(level=logging.DEBUG)
    logger.info('Launching multi')
    tickers = si.tickers_sp500()
    
    p = Pool(10)
    result = p.map_async(get_and_store_news, tickers)
    result.get()
