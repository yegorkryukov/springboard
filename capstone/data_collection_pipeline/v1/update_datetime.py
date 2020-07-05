import pymongo as pm
import pandas as pd
from yahoo_fin import stock_info as si 
from multiprocessing import Pool
import logging
from newspaper import Article
from datetime import datetime

def update_datetime(t):
    """
    Parses all articles for `t` ticker and updates
    the appropriate MongoDB news.datetime element 
    of `ticker` document.
    """
    logger.info(f'Working === {t} ===')

    news = collection.find_one({'ticker' : t})['news']

    for n in news:
        dt = pd.to_datetime(n['datetime'])
        if pd.isnull(dt): 
            try:
                article = Article(n['url'])
                article.download()
                article.parse()
                dt = pd.to_datetime(article.publish_date)
            except Exception as e:
                logger.info(f"Failed to download {t} datetime for URL: {n['url']} \n {e}")
                continue

            if pd.isnull(dt):
                logger.info(f"Failed to update {t} datetime for URL: {n['url']}")
                continue
            else:
                collection.update_one(
                    { 'ticker' : t},
                    { '$set': { 'news.$[elem].datetime' : dt } },
                    array_filters = [ { 'elem.url' : { '$eq' : n['url'] } } ]
                )
                logger.debug(f"Updated {t} with date {dt} for URL: {n['url']}")
        else:
            collection.update_one(
                    { 'ticker' : t},
                    { '$set': { 'news.$[elem].datetime' : dt } },
                    array_filters = [ { 'elem.url' : { '$eq' : n['url'] } } ]
                )
            logger.debug(f"Datetime was ok, converted the type in MongoDB")
        
        # break


logger = logging.getLogger(__name__)        
logging.basicConfig(level=logging.INFO)

client = pm.MongoClient('mongodb://localhost:27017')
collection = client['news']['recommendations']

if __name__ == '__main__': 
    
    logger.info(f'Starting updating datetime at {datetime.now()}')
    tickers = si.tickers_sp500()
    # tickers= ['MSFT']
    
    p = Pool()
    result = p.map_async(update_datetime, tickers)
    p.close()
    p.join()
    logger.info(f'Finished at {datetime.now()}')