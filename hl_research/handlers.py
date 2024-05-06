import queue
import time 
from loguru import logger 

from hl_research.hl_types import L2BookMsg, TradesMsg, L2Level


sizes = [1e3, 1e4, 1e5]

q = queue.Queue()
def q_size():
    return q.qsize()
def q_get():
    return q.get()

def get_aggregate_price(levels: list[L2Level], sizes_usd: list[float]) -> list[float]:
    size = 0 
    price = 0 
    prices: list[float] = [] 
    j = 0
    for l in levels: 
        px = float(l['px'])
        sz = float(l['sz'])
        while sz>0:
            s = min(sizes_usd[j]-size, sz*px)
            price = (size*price+s*px)/(size+s)
            size += s 
            sz -= s/px 
            if size == sizes_usd[j]:
                prices.append(price) 
                j+=1 
                if j == len(sizes_usd):
                    return prices 
    return prices 

def trades_handler(msg: TradesMsg):
    if not (trades := msg['data']):
        return
    time_received = time.time()*1000
    for t in trades:
        t['time_received'] = time_received
    q.put(('trades', msg['data']))
    
def book_handler(msg: L2BookMsg):
    coin = msg['data']['coin']
    t = msg['data']['time']
    time_received = time.time()*1000
    levels = msg['data']['levels']
    bids = get_aggregate_price(levels[0], sizes)
    asks = get_aggregate_price(levels[1], sizes)
    book_data = [{
        'coin': coin, 
        'time_received': time_received, 
        'time':t, 
        'sz': s, 
        'bid': b, 
        'ask': a 
        } for s, b, a in zip(sizes, bids, asks)]
    q.put(('book', book_data))