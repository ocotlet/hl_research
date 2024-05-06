from loguru import logger 
import csv 
import time 
import os 
import sys 
import dotenv

from hl_research.ws import WebsocketManager
from hl_research.handlers import book_handler, trades_handler, q_get, q_size

coins = ['BTC', 'ETH', 'DOGE']

def log_config():
    dotenv.load_dotenv(dotenv.find_dotenv())
    log_level = os.environ['LOG_LEVEL'] if 'LOG_LEVEL' in os.environ else 'INFO'
    logger.remove()
    logger.add(sys.stderr, level=log_level)

def main():
    log_config()

    with WebsocketManager('http://api.hyperliquid.xyz') as ws, open(f'data/trades.csv', 'a') as f, open(f'data/l2Book.csv', 'a') as g:
    
        wt = csv.writer(f, delimiter=',')
        wb = csv.writer(g, delimiter=',')

        for c in coins: 
            ws.subscribe({'type': 'l2Book', 'coin': c}, book_handler)
            ws.subscribe({'type': 'trades', 'coin': c}, trades_handler)
            
        while ws.ws.keep_running:
            time.sleep(60)
            logger.info('Flushing queue to csv files')
            while q_size():
                t, d = q_get()
                for r in d:
                    data = list(r.values())
                    logger.debug(f'writing {data=} in {t=}')
                    w = wt if t == 'trades' else wb 
                    w.writerow(data)
            logger.info('Done flushing')
    
