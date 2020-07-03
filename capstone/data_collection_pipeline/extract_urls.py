def get_html_from_url(url):
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

    result = get_html_from_url(url)

    if result:
        html = BeautifulSoup(result, 'html.parser')
        news_table = html.find(id='news-table')

        urls = [row.a['href'] for row in news_table.findAll('tr')]
        logging.info(f'Found {len(urls)} URLs at finviz.com for {ticker}')
        return urls
    logging.info(f'No URLs found at finviz.com for {ticker}')
    return False

def get_urls_yahoo(ticker):
    """Obtain latest news for `ticker` from finance.yahoo.com

    Parameters
    ----------
    ticker :  str, ticker to collect news for

    Output
    ------
    urls   : list, list of urls
    """
    from selenium import webdriver
    import time
    from random import randint
    from selenium.webdriver.firefox.options import Options

    js = """var scrollingElement = (document.scrollingElement || document.body);
                    scrollingElement.scrollTop = scrollingElement.scrollHeight;"""

    url = f'https://finance.yahoo.com/quote/{ticker}'
    urls_list = set()
    
    try: 
        options = Options()
        options.add_argument("--headless")
        browser = webdriver.Firefox(options=options, executable_path=r'geckodriver')
        browser.get(url)
        logging.info(f'Headless Firefox Initialized for URL: {url}')
        if browser.current_url == f'https://finance.yahoo.com/lookup?s={ticker}':
            logging.info(f'Extracting URLs failed. Ticker {ticker} does not exist')
            return False
        browser.execute_script(js)
        time.sleep(randint(3,10))
        items_list = browser.find_elements_by_xpath('//h3/a')
        num_of_items = 0
        while num_of_items != len(items_list):
            num_of_items = len(items_list)
            browser.execute_script(js)
            time.sleep(randint(3,5))
            items_list = browser.find_elements_by_xpath('//h3/a')
            logging.info(f'{ticker} found {len(items_list)} urls so far')

        for item in items_list:
            urls_list.add(item.get_attribute('href'))

        logging.info(f'Found {len(urls_list)} urls for {ticker}')
    except Exception as e:
        logging.info(f'Extracting URLs failed. Error:\n{e}')

    browser.quit()
    if urls_list:
        return list(urls_list)
    logging.info(f'No URLs found at finance.yahoo.com for {ticker}')
    return False

def save_urls_to_db(urls, ticker=''):
    """Saves urls to MongoDB checking for duplicates
    """
    import pymongo as pm
    import pandas as pd
    import logging

    logging.info(f'Got {len(urls)} URLs to save for ticker {ticker}')

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

        qty_stored_to_process_before = c.find_one(
            {'ticker':ticker},
            {'urls_to_process':1, '_id':0}
        )

        if len(qty_stored_to_process_before) > 0:
            qty_stored_to_process_before = len([
                _ for _ 
                in qty_stored_to_process_before['urls_to_process']
            ])
        else: qty_stored_to_process_before = 0
        
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



        logging.info(f'Saved {len(to_process_urls) - qty_stored_to_process_before} new urls for {ticker}')
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
    logging.info(f'Starting URL extraction')

    tickers = ['A']
    for ticker in tickers:
        urls_finviz = get_urls_finviz(ticker)
        print(urls_finviz)
        if urls_finviz: save_urls_to_db(urls_finviz, ticker=ticker)

        # urls_yahoo = get_urls_yahoo(ticker)
        # if urls_yahoo: save_urls_to_db(urls_yahoo, ticker=ticker)


    logging.info('Extraction finished')





