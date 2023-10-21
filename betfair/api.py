import hashlib
import logging
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from flask_jwt_extended import jwt_required
from pydantic import BaseModel, Field

from betfair.config import admin_collection

log = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You might want to be more specific in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# exception handler for authjwt
# in production, you can tweak performance using orjson response


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

# provide a method to create access tokens. The create_access_token()
# function is used to actually generate the token to use authorization
# later in endpoint protected


class User(BaseModel):
    email: str
    password: str


@app.post('/login')
def login(user: User, Authorize: AuthJWT = Depends()):
    if verify_user(user.email, user.password):
        # subject identifier for who this token is for example id or username from database
        access_token = Authorize.create_access_token(subject=user.email)
        log.info(access_token)
        return {"access_token": access_token}

# protect endpoint with function jwt_required(), which requires
# a valid access token in the request headers to access.


@app.get('/user')
def user(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

    current_user = Authorize.get_jwt_subject()
    return {"user": current_user}


def verify_user(login, password, ip=None, computer_name=None):
    expiry_date = datetime.today() - timedelta(days=35)
    entries = list(admin_collection.find(
        {"login": login,
         "password": makemd5(password),
         "timestamp": {"$gte": expiry_date}
         }
    ))

    if ip and len(entries):
        admin_collection.update_one({'login': login},
                                    {'$addToSet': {'ip':  ip}})

    if computer_name and len(entries):
        admin_collection.update_one({'login': login},
                                    {'$addToSet': {'computer_name':  computer_name}})

    return len(entries)


def makemd5(key_string):
    new_key_string = key_string.encode('utf-8')
    return (hashlib.md5(new_key_string).hexdigest())


@app.post("/add_user")
def add_user(login, password, admin_password, expiry_days):
    expiry_date = datetime.today() + timedelta(days=int(expiry_days))
    if admin_password == "donald11":
        admin_collection.update_one({'login': login},
                                    {'$set': {'password':  makemd5(password),
                                              'timestamp': expiry_date}}, upsert=True)


def verify_user(login, password, ip=None, computer_name=None):
    expiry_date = datetime.today() - timedelta(days=35)
    entries = list(admin_collection.find(
        {"login": login,
         "password": makemd5(password),
         "timestamp": {"$gte": expiry_date}
         }
    ))

    if ip and len(entries):
        admin_collection.update_one({'login': login},
                                    {'$addToSet': {'ip':  ip}})

    if computer_name and len(entries):
        admin_collection.update_one({'login': login},
                                    {'$addToSet': {'computer_name':  computer_name}})

    return len(entries)
