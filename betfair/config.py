"""Connection routines"""

import socket

import betfairlightweight
from pymongo import MongoClient

USERNAME = "default"
HOSTNAME = '127.0.0.1'
MONGO_USERNAME = "sickpunt"
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
admin_collection = mongo_db["user_admin"]

admin_data = list(admin_collection.find(
    {"Email": USERNAME}, {'_id': False}))[0]

APP_KEY = admin_data['BetfairToken']
PASSWORD = admin_data['BetfairPassword']
USERNAME = admin_data['BetfairLogin']

# constants
COUNTRIES = ['AU', 'UK', 'IE']
MARKET_TYPES = ['WIN', 'PLACE']
MAX_RACE_STREAMS = 50

EVENT_TYPE_IDS = ['7']  # Horse Racing event type ID
KEEP_AFTER_RACE_START_MIN = 60
HOURS_TO_FETCH = 6

SERVER_NAMES = ['ip-172-31-35-26.ap-southeast-2.compute.internal']

SECS_MARKET_FETCH_INTERVAL = 60

client = betfairlightweight.APIClient(
    username=USERNAME, password=PASSWORD, app_key=APP_KEY)
client.login_interactive()


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


tick_sizes = [(1.01, 2, 0.01),
              (2.02, 3, 0.02),
              (3.05, 4, 0.05),
              (4.1, 6, 0.1),
              (6.2, 10, 0.2),
              (10.5, 20, 0.5),
              (21, 30, 1.),
              (32, 50, 2.),
              (55, 100, 5.),
              (110, 1000, 10.)]
