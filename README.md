# Hyperliquid research 
This repo connects to the Hyperliquid websocket and subscribes to book and trade data for three coins: BTC, ETH and DOGE. 
For the book data it saves the bid/ask for $1k $10k and $100k market orders, just because we don't need to look at the full order book for this simple exercise. 

Trade and book data are saved to data/l2Book.csv and data/trades.csv files. For efficiency, websocket data are handled in separate threads and the data put in a queue. Every minute the queue is dumped in the csv files. 

## Running docker image 
After building the docker image we should run it with 
```sudo docker run -v $PWD/hl_research/data:/data --restart always --name hl_research -d hl_research```
It will create csv files in the data folder with the names l2Book.csv and trades.csv where this data will be saved (or append to them if they already exist)

## Suggested improvements
If we want to improve on this exercise we could have multiple docker containers running on multiple machines and save data to a centralized location like a database. Then we can keep only the first row per each table, instrument and timestamp which should be faster. 
We could also try creating multiple websocket connections in the same script and keep only the one that is fastest.  