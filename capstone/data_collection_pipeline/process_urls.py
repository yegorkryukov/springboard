def detect_and_move(ticker):
    """Looks up for a document in one collection
    and moves to another one if finds direct mentions
    of `ticker` in the url's article text. Downloads article
    text if needed
    """
    from bson.objectid import ObjectId
    import pymongo as pm
    import logging
    import re

    client = pm.MongoClient('mongodb://localhost:27017')
    source_collection = client['news']['not_processed']
    target_collection = client['news']['recommendations']

    source_doc = source_collection.find_one({'$text': {'$search': ticker}})
    logging.info(f"{ticker}: found document. _id: {source_doc['_id']}")

    if 'text' in source_doc.keys():
        target_collection.update_one(
            {'ticker' : ticker},
            {'$addToSet':
             {'news':
              {
                'url'      : source_doc['url'],
                'date'     : source_doc['date'],
                'title'    : source_doc['title'],
                'text'     : " ".join(re.split(r'[\n\t]+', source_doc['text'])),
                'keywords' : source_doc['keywords'],
                'summary'  : source_doc['summary']
              }
             }      
            },
                upsert=True
            )
        logging.info(f"Added article to {target_collection.name}. URL: {source_doc['url']}")
        source_collection.delete_one({'_id': ObjectId(source_doc['_id'])})
        logging.info(f"Deleted article {ObjectId(source_doc['_id'])} from {source_collection.name}")
        return True
    else:
        print('need to finish')
        return False

if __name__ == '__main__': 
    import logging
    from yahoo_fin import stock_info as si 

    logger = logging.getLogger()
    handler = logging.FileHandler('logs/process_url.log')
    formatter = logging.Formatter(
            '%(asctime)s| %(levelname)s| %(message)s')
    handler.setFormatter(formatter)
    if not len(logger.handlers): 
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    logging.info(f'Starting URL processing')

    ticker = 'AAPL'
    detect_and_move(ticker)

    logging.info(f'URL processing ended')