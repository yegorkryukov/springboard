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
    from random import randint
    import multiprocessing
    logger = multiprocessing.get_logger()

    UA = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'Mozilla/5.0 CK={} (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
    ]

    logger.info(f'Getting html from {url}')
    headers = {"User-Agent":UA[randint(0,len(UA)-1)]}
    requests.adapters.DEFAULT_RETRIES = 1

    try:
        url_get = requests.get(url, headers=headers, timeout=3)
        if url_get.status_code == 200:
            logger.info(f'Successfully got html for {url}')
            return url_get.text
        else:
            logger.info(f'Cannot get html for {url}. Error: {url_get.status_code}')
            return False
    except Exception as e:
        logger.info(f'Cannot get html for {url}. Error: {e}')
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
    import re
    import multiprocessing
    logger = multiprocessing.get_logger()

    logger.info(f"Processing {url}")
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

        logger.info(f'Extracted {article.title} from {url}')
        return {
            'url'      : url,
            'date'     : article.publish_date,
            'title'    : article.title,
            'text'     : " ".join(re.split(r'[\n\t]+', article.text)),
            'keywords' : article.keywords,
            'summary'  : article.summary
        }
    else:
        logger.info(f'Could not extract data from {url}')
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
    import multiprocessing
    logger = multiprocessing.get_logger()

    client = pm.MongoClient('mongodb://localhost:27017')
    c = client['news']['recommendations']

    
    logger.info(f'Processing {ticker}')

    urls_to_process = c.find_one(
            {'ticker':ticker},
            {'urls_to_process':1, '_id':0}
        )

    if len(urls_to_process) > 0:
        urls_to_process = urls_to_process['urls_to_process']
        logger.info(f'Found {len(urls_to_process)} URLs to scrape')
    else:
        logger.info(f'No URLs found in {c} to process for {ticker}')
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
            logger.info(f"Saved title {doc['title']} for {url} to DB")

            # deletes processed url
            c.update_one(
                {'ticker' : ticker},
                {'$pull'  : {"urls_to_process" : url}}
            )
            logger.info(f'Deleted from DB URL {url}')

            scraped += 1
        else:
            logger.info(f'Did not get the text for {url}')
    
    logger.info(f'{ticker}: Scraped {scraped} our of {len(urls_to_process)} URLs')


# def setup_logger():
#     logger = logger.getLogger()
#     handler = logger.FileHandler('logs/text_extraction.log')
#     formatter = logger.Formatter(
#             '%(asctime)s| %(levelname)s| %(message)s')
#     handler.setFormatter(formatter)
#     if not len(logger.handlers): 
#         logger.addHandler(handler)
#     logger.setLevel(logger.INFO)

# Start MongoDB
# !brew services start mongodb-community@4.2

# Stop MongoDB
# !brew services stop mongodb-community@4.2

if __name__ == '__main__': 
    from yahoo_fin import stock_info as si 
    from multiprocessing import Pool
    import multiprocessing, logging

    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)

    # setup_logger()

    logger.info('Starting text extraction')

    p = Pool()
    tickers = si.tickers_sp500()
    result = p.map_async(scrape_urls, tickers)
    p.close()
    p.join()

    logger.info(f'Finished text extraction')