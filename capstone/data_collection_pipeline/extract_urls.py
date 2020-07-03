def get_text_from_url(url):
    """Returns html content of the page at url 
    """
    import requests
    import logging
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) Gecko/20100101 Firefox/79.0"}
    requests.adapters.DEFAULT_RETRIES = 1

    url_get = requests.get(url, headers=headers, timeout=3)
    if url_get.status_code == 200:
        return url_get.text
    logging.info(f'Cannot get html for {url}. Error: {url_get.status_code}')
    return False

def get_urls_finviz(ticker):
    """Obtain latest news for `ticker` from finviz.com

    Parameters
    ----------
    ticker :  str, ticker to collect news for

    Output
    ------
    urls   : list, list of urls
    """
    import logging
    from bs4 import BeautifulSoup

    logging.info(f'Getting finviz.com news urls for {ticker}')

    url = 'https://finviz.com/quote.ashx?t=' + str(ticker)

    result = get_text_from_url(url)

    if result:
        html = BeautifulSoup(result, 'html.parser')
        news_table = html.find(id='news-table')

        urls = [row.a['href'] for row in news_table.findAll('tr')]
        logging.info(f'Found {len(urls)} URLs at finviz.com for {ticker}')
        return urls
    logging.info(f'No URLs found at finviz.com for {ticker}')
    return False
            
def save_urls_to_db(urls, ticker=''):
    """Saves urls to MongoDB checking for duplicates
    """
    import pymongo as pm
    import pandas as pd
    import logging

    client = pm.MongoClient('mongodb://localhost:27017')

    if  ticker and urls:
        DB_NAME = 'news'
        COLLECTION_NAME = 'recommendations'
        db = client[DB_NAME]
        c = db[COLLECTION_NAME]
        
        processed_urls = c.find_one(
            {'ticker':ticker},
            {'news.url':1, '_id':0}
        )
        
        if len(processed_urls) > 0:
            processed_urls = [
                _['url'] for _ 
                in processed_urls['news']
            ]
            to_process_urls = [
                _ for _ 
                in urls 
                if _ not in processed_urls
            ]
        else: to_process_urls = urls

        # $addToSet operator adds a value to an array 
        # unless the value is already present
        # $each modifier allows the $addToSet operator 
        # to add multiple values to the array 
        c.update_one(
            {'ticker' : ticker},
            {'$addToSet': 
                {'urls_to_process' : 
                    { '$each': to_process_urls}
                }
            },
            upsert = True
        )

        logging.info(f'Saved <= {len(to_process_urls)} new urls for {ticker}')
    # else:
        # collection = client['news']['not_processed']
        # check for duplicates
        
        # save to news.not_processed collection


if __name__ == '__main__': 
    import logging
    import datetime

    logger = logging.getLogger()
    handler = logging.FileHandler('logs/extract_urls.log')
    formatter = logging.Formatter(
            '%(asctime)s| %(levelname)s| %(message)s')
    handler.setFormatter(formatter)
    if not len(logger.handlers): 
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    logging.info(f'Starting url extraction at {datetime.datetime.now()}')

    ticker = 'A'
    urls = get_urls_finviz(ticker)
    if urls: 
        save_urls_to_db(urls, ticker=ticker)
    
    logging.info('Extraction finished')





