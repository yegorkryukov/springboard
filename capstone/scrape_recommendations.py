import pymongo as pm
import requests
from yahoo_fin import stock_info as si 
from datetime import date
import logging
from multiprocessing import Pool

def get_recommendation(ticker):
    """
    Obtaines yahoo recommendations for a 'ticker'
    """
    logger.info(f'Processing {ticker}')
    lhs_url = 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/'
    rhs_url = '?formatted=true&crumb=swg7qs5y9UP&lang=en-US&region=US&' \
              'modules=upgradeDowngradeHistory,recommendationTrend,' \
              'financialData,earningsHistory,earningsTrend,industryTrend&' \
              'corsDomain=finance.yahoo.com'
              
    url =  lhs_url + ticker + rhs_url
    r = requests.get(url)
    if not r.ok:
        recommendation = 6
    try:
        result = r.json()['quoteSummary']['result'][0]
        recommendation =result['financialData']['recommendationMean']['fmt']
    except:
        recommendation = 6
    
    return recommendation

def get_and_store_recommendations(ticker, dt=None):
    """
    Retrieves yahoo recommendations for a 'ticker' and stores to MongoDB avoiding duplicates
    """
    
    day = date.today().strftime('%Y-%m-%d') if dt is None else dt

    doc = {
        'recommendations': {
            'date' : day,
            'recommendation' : get_recommendation(ticker)
        }
    }
    
    collection.update_one(
        {'ticker' : ticker},
        {'$addToSet': doc},
        upsert = True
    )
    print(f"Saved {ticker}: {doc}")
    return doc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = pm.MongoClient('mongodb://localhost:27017')
collection = client['news']['recommendations']

if __name__ == '__main__': 
    logger.info('Getting stock recommendations for sp500')

    tickers = si.tickers_sp500()

    p = Pool()
    result = p.map_async(get_and_store_recommendations, tickers)
    p.close()
    p.join()
