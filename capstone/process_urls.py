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

    g = Goose()
    
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) Gecko/20100101 Firefox/79.0"}
    cookies = {"cookie":"prov=f155b877-1d05-46c0-e4c8-06710700ab38; _ga=GA1.2.517998572.1588979467; __gads=ID=dff7ccb26af6d704:T=1588979467:S=ALNI_MYjeHrNVGWFTWjnWwl91eovS3W_MQ; __qca=P0-1509564436-1588979467447; _gid=GA1.2.1286355178.1593617896; _gat=1"}


    
    try:
        url_get = requests.get(url, cookies=cookies, headers=headers)
        article = g.extract(raw_html=url_get.text)
        
        collection.update_one(
        {'url' : url},
        {'$set':
                {
                    'date'     : article.publish_date,
                    'title'    : article.title,
                    'text'     : article.cleaned_text,
                    'keywords' : article.meta_keywords,
                    'summary'  : article.meta_description
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
import logging
from multiprocessing import Pool
import datetime
from goose3 import Goose
import requests


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
