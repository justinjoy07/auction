from  uvicorn import run
import random
import sys
import time
from fastapi import FastAPI


SERVER_PORT = sys.argv[1]
BIDDER_ID = sys.argv[2]

app = FastAPI()


@app.get("/bid")
def bid():
    """
    Generates a random bid value after a certain delay
    """
    delay = random.uniform(10/1000.0, 500/1000.0)
    bid_value = random.uniform(1,10)
    time.sleep(delay)
    return {"bidder_id": BIDDER_ID,
            "bid_value": bid_value}

run(app, host="localhost", port=SERVER_PORT)