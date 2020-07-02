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

def get_urls_finwiz(ticker):
    """Obtain latest news for `ticker` from finwiz.com

    Parameters
    ----------
    ticker :  str, ticker to collect news for

    Output
    ------
    urls   : list, list of urls
    """
    import logging
    from bs4 import BeautifulSoup

    logging.info(f'Getting finwiz.com news urls for {ticker}')

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
            


ticker = 'A'
print(get_urls_finwiz(ticker))





