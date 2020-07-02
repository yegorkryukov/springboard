def scrape(url):
    """
    Scrapes an article from the 'url' 
    
    Parameters:
    --------
    url         : str, url to scrape
    
    Returns:
    --------
    Article's html and features stored to db, 
    
    """
    logging.info(f"Processing {url}")
    
    try:
        article = Article(url)
        article.download()
        # the below method may only extract a snippet... 
        # check the database for results of text extraction
        # and apply additional processing if needed after 
        # article has been stored in the DB
        # see code below Newrepublic for example
        article.parse()
        article.nlp()
        
        collection.update_one(
        {'url' : url},
        {'$set':
                {
                    # 'html'     : article.html,
                    'date'     : article.publish_date,
                    'title'    : article.title,
                    'text'     : article.text,
                    'keywords' : article.keywords,
                    'summary'  : article.summary
                }
        },
            upsert=True
        )
        logging.info(f'Saved {url} to DB')
        return
    except Exception as e:
        logging.info(f'Data not saved. Error: {e}')
        return

import pymongo as pm
import pandas as pd
from newspaper import Article
import logging
from multiprocessing import Pool
import datetime

# Start MongoDB
# !brew services start mongodb-community@4.2

# Stop MongoDB
# !brew services stop mongodb-community@4.2



# use multiprocessing to extract features
if __name__ == '__main__': 
    logger = logging.getLogger()
    handler = logging.FileHandler('content_extraction.log')
    formatter = logging.Formatter(
            '%(asctime)s| %(levelname)s| %(message)s')
    handler.setFormatter(formatter)
    if not len(logger.handlers): logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    logging.info(f'Starting url extraction at {datetime.datetime.now()}')
    
    client = pm.MongoClient('mongodb://localhost:27017')
    collection = client['news']['not_processed']
    
    saved_urls = [
        rec['url'] for rec in collection.find({}, {'url':1, 'qty':1})
    ]
    
    to_process_urls = list(pd.read_csv('media/usanews_2015_2020.csv',index_col=0).url)
    for url in to_process_urls:
        if url not in saved_urls: scrape(url)
    
    logging.info(f'Finished at {datetime.datetime.now()}')
