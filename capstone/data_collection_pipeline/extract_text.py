def get_html_from_url(url):
    """Returns html content of a page at `url` 

    Parameters:
    --------
    url         : str, url to scrape
    
    Returns:
    --------
    html        : str, html of the page
    False       : bool, if get request fails
    """
    import requests
    import logging
    from random import randint
    from fake_useragent import UserAgent
    # UA = UserAgent()
    UA = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'Mozilla/5.0 CK={} (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
    ]

    logging.info(f'Getting html from {url}')
    headers = {"User-Agent":UA[randint(0,len(UA)-1)]}
    requests.adapters.DEFAULT_RETRIES = 1

    try:
        url_get = requests.get(url, headers=headers, timeout=3)
        if url_get.status_code == 200:
            logging.info(f'Successfully got html for {url}')
            return url_get.text
        else:
            logging.info(f'Cannot get html for {url}. Error: {url_get.status_code}')
            return False
    except Exception as e:
        logging.info(f'Cannot get html for {url}. Error: {e}')
        return False

def scrape(url):
    """
    Scrapes an article from the 'url', extracts meta data using Nespaper3K package
    
    Parameters:
    --------
    url         : str, url to scrape
    
    Returns:
    --------
    doc         : dict,
        {
            'url'      : url,
            'date'     : article publish_date,
            'title'    : article title,
            'text'     : article cleaned_text,
            'keywords' : article meta_keywords,
            'summary'  : article summary
        }
    False       : bool, if get request fails
    """
    from newspaper import Article, Config
    import logging
    import re

    logging.info(f"Processing {url}")
    config = Config()
    config.memoize_articles = False
    config.fetch_images = False
    config.language = 'en'
    config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) Gecko/20100101 Firefox/79.0'
    config.request_timeout = 5
    config.number_threads = 8

    html = get_html_from_url(url)

    if html and len(html)>300:
        article = Article(url=url, config=config)
        article.download_state = 2
        article.html = html
        article.parse()
        article.nlp()

        logging.info(f'Extracted {article.title} from {url}')
        return {
            'url'      : url,
            'date'     : article.publish_date,
            'title'    : article.title,
            'text'     : " ".join(re.split(r'[\n\t]+', article.text)),
            'keywords' : article.keywords,
            'summary'  : article.summary
        }
    else:
        logging.info(f'Could not extract data from {url}')
        return False

def scrape_urls(ticker):
    """Processes all urls stored in MongoDB document with `ticker.not_processed` field

    Parameters
    ----------
    ticker     : str, ticker to process

    Output
    ------
    Obtains list of urls from news.recommendations.ticker.urls_to_process, downloads html and saves
    meta data to news.recommendations.ticker.news document.
    """
    import pymongo as pm
    import logging

    client = pm.MongoClient('mongodb://localhost:27017')
    c = client['news']['recommendations']

    logging.info(f'Processing {ticker}')

    urls_to_process = c.find_one(
            {'ticker':ticker},
            {'urls_to_process':1, '_id':0}
        )

    if len(urls_to_process) > 0:
        urls_to_process = urls_to_process['urls_to_process']
        logging.info(f'Found {len(urls_to_process)} URLs to scrape')
    else:
        logging.info(f'No URLs found in {c} to process for {ticker}')
        return False
    
    scraped = 0
    for url in urls_to_process:
        doc = scrape(url)
        if doc:
            c.update_one(
                {'ticker'   : ticker},
                {'$addToSet': {'news' : doc}},
                upsert=True
            )
            logging.info(f"Saved title {doc['title']} for {url} to DB")

            # deletes processed url
            c.update_one(
                {'ticker' : ticker},
                {'$pull'  : {"urls_to_process" : url}}
            )
            logging.info(f'Deleted from DB URL {url}')

            scraped += 1
            break # for testing
        else:
            logging.info(f'Did not get the text for {url}')
    
    logging.info(f'{ticker}: Scraped {scraped} our of {len(urls_to_process)} URLs')


def setup_logging():
    logger = logging.getLogger()
    handler = logging.FileHandler('logs/text_extraction.log')
    formatter = logging.Formatter(
            '%(asctime)s| %(levelname)s| %(message)s')
    handler.setFormatter(formatter)
    if not len(logger.handlers): 
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Start MongoDB
# !brew services start mongodb-community@4.2

# Stop MongoDB
# !brew services stop mongodb-community@4.2

if __name__ == '__main__': 
    from yahoo_fin import stock_info as si 
    # from multiprocessing import Pool
    import logging
    setup_logging()

    logging.info('Starting text extraction')
    
    for ticker in si.tickers_sp500():
        scrape_urls(ticker)
        break # for testing

    logging.info(f'Finished text extraction')