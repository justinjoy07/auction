from  uvicorn import run
import threading  
import os
import sys 
import multiprocessing

import random
import requests
import time
from typing import Optional
from fastapi import FastAPI, Response
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor, as_completed

processes = []
results = []
bidders= []
ports = list(range(8001,10000))


app = FastAPI()


class BidderThread(threading.Thread):  
    """
    Thread to run each bidder server
    """
    def __init__(self, port, bidder_id):  
        threading.Thread.__init__(self)  
        self.port = port  
        self.bidder_id = bidder_id
        # helper function to execute the threads 
    def run(self):  
        os.system(f"python3 bidder.py {self.port} {self.bidder_id}")


class Auction(BaseModel):
    """
    Auction Model
    """
    auction_id: str

class Bidder(BaseModel):
    """
    Bidder Model
    """
    bidder_id: str
    bidder_port: int = 0


@app.post("/register")
def register(bidder: Bidder, response: Response):
    """
    Register a bidder with a given bidder_id with a unique port
    """
    global bidders
    if bidder.bidder_id not in [b.bidder_id for b in bidders]:
        bidder.bidder_port = get_port()
        th = BidderThread(bidder.bidder_port, bidder.bidder_id)
        th.start()
        bidders.append(bidder)
        response.status_code = 201
        message = "Bidder Registered"
    else:
        response.status_code = 200
        message = "Bidder Already Registered"
    return message

@app.get("/list")
def list_endpoints():
    """
    Lists all bidder endpoints
    """
    global bidders
    return [f"http://localhost:{bidder.bidder_port}" for bidder in bidders]

def get_port():
    """
    Assigns a unique port
    """
    global ports
    port = random.choice(ports)
    ports.remove(port)
    return port

def get_bid(port):
    """
    Requests bidder to bid and returns bid_amount and bidder_id
    """
    return requests.get(f"http://localhost:{port}/bid").json()

@app.post("/auction")
def auction(auction: Auction, response: Response):
    """
    Starts a new process to run the auction
    """
    print(f"Starting Auction: {auction.auction_id}")
    start = time.time()
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    return_dict['result'] = {'bid_value': 0}
    p = multiprocessing.Process(target=run_auction, name="Foo", args=(return_dict,))
    p.start()
    #Running tasks for 200ms
    p.join(200/1000.0)
    print(f"Time taken: {time.time() - start}")
    if return_dict['result']['bid_value'] == 0:
        response.status_code = 404
        return {}
    return return_dict['result']

def run_auction(return_dict):
    """
    Sends requests to all registered bidders and 
    returns largest bidder_id and bid_amount
    """
    global bidders
    with ThreadPoolExecutor(max_workers=len(bidders)) as executor:
        for bidder in bidders:
            processes.append(executor.submit(get_bid, bidder.bidder_port))
        for task in as_completed(processes):
            if task.result()['bid_value'] > return_dict['result']['bid_value']:
                return_dict['result'] = task.result()
                print(f"Bid Recievied: {task.result()}")



run(app, host="localhost", port=8000)