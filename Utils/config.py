from pymongo import MongoClient, DESCENDING
from firebase_admin import credentials
from dotenv import load_dotenv
import firebase_admin
import os

firebase_admin.initialize_app(credentials.Certificate("serviceAccountKey.json"))
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET")
JWT_ACCESS_TOKEN_EXPIRES = 900
JWT_REFRESH_TOKEN_EXPIRES = 2592000
admins = [{"id": 1, "username": "admin@sukoon.love", "password": "Care@sukoon123"}]

client = MongoClient(os.getenv("PROD_DB_URL"))
db = client["test"]

deleted_schedules_collection = db["deletedschedules"]
deleted_experts_collection = db["deletedexperts"]
applications_collection = db["becomesaarthis"]
deleted_users_collection = db["deletedusers"]
fcm_tokens_collection = db["fcm_tokens"]
categories_collection = db["categories"]
statuslogs_collection = db["statuslogs"]
schedules_collection = db["schedules"]
experts_collection = db["experts"]
logs_collection = db["errorlogs"]
calls_collection = db["calls"]
users_collection = db["users"]
meta_collection = db["meta"]


calls_collection.create_index([("initiatedTime", DESCENDING)])
experts_collection.create_index([("createdDate", DESCENDING)])
users_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("status", 1)])


experts_cache = {}
call_threads = {}
users_cache = {}
