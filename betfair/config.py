"""Connection routines"""

import socket

import betfairlightweight
from pymongo import MongoClient

APP_KEY = "mECg2P2ohk92MLXy"
PASSWORD = r"%2s8ThBv&u5#s$Wg"
USERNAME = "penjud"

client = betfairlightweight.APIClient(
    username=USERNAME, password=PASSWORD, app_key=APP_KEY)
client.login_interactive()


HOSTNAME = '3.24.169.161'
MONGO_USERNAME = "admin"
MONGO_PASSWROD = "sickpunt123"
MONGO_DB = "horse_racing"  # The database you want to connect to
MONGO_AUTH_DB = "admin"  # Database where the user is authenticated
connection_string = (f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWROD}@{HOSTNAME}:27017/{MONGO_DB}"
                     f"?authSource={MONGO_AUTH_DB}")

mongo_client = MongoClient(connection_string)
mongo_db = mongo_client["horse_racing"]
metadata_collection = mongo_db["metadata"]
punters_com_au_collection = mongo_db["punters_com_au"]
tickdata_collection = mongo_db["tickdata"]
orders_collection = mongo_db["orders"]
strategy_collection = mongo_db["strategies"]

# constants
COUNTRIES = ['AU']
MARKET_TYPES = ['WIN']
EVENT_TYPE_IDS = ['7']  # Horse Racing event type ID

SERVER_NAMES = ['ip-172-31-35-26.ap-southeast-2.compute.internal']

SECS_MARKET_FETCH_INTERVAL = 60


def upsert_event_metadata(race_data):
    # upsert the market data into the MongoDB collection
    for race in race_data:
        # use upsert=True to avoid duplicates
        metadata_collection.update_one(
            {'market_id': race['marketId']},
            {
                '$set': race
            },
            upsert=True,
        )


def is_prod_computer():
    return socket.gethostname() in SERVER_NAMES
