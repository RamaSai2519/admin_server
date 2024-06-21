from pymongo import MongoClient, DESCENDING
from firebase_admin import credentials
from dotenv import load_dotenv
import firebase_admin
import boto3
import os

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET")
FB_SERVER_KEY = os.getenv("FB_SERVER_KEY")
REGION = os.getenv("REGION")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")

firebase_admin.initialize_app(
    credentials.Certificate("serviceAccountKey.json"))

s3_client = boto3.client(
    "s3",
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY
)

client = MongoClient(os.getenv("PROD_DB_URL"))
db = client["test"]
gamesdb = client["games"]

games_config_collection = gamesdb["games_config"]

deleted_schedules_collection = db["deletedschedules"]
deleted_experts_collection = db["deletedexperts"]
applications_collection = db["becomesaarthis"]
deleted_users_collection = db["deletedusers"]
eventconfigs_collection = db["eventconfigs"]
fcm_tokens_collection = db["fcm_tokens"]
categories_collection = db["categories"]
schedules_collection = db["schedules"]
callsmeta_collection = db["callsmeta"]
errorlogs_collection = db["errorlogs"]
timings_collection = db["timings"]
experts_collection = db["experts"]
events_collection = db["events"]
admins_collection = db["admins"]
shorts_collection = db["shorts"]
calls_collection = db["calls"]
users_collection = db["users"]
meta_collection = db["meta"]

calls_collection.create_index([("initiatedTime", DESCENDING)])
experts_collection.create_index([("createdDate", DESCENDING)])
users_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("status", 1)])

experts_cache = {}
users_cache = {}
subscribers = {}
players = {}

ALLOWED_MIME_TYPES = [
    "image/jpeg", "image/pipeg", "image/png", "application/octet-stream",
    "image/svg+xml", "video/mp4", "video/webm", "video/quicktime",
    "video/x-matroska"
]
