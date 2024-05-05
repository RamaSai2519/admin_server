import requests
from flask import jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import threading
import pytz
from time import sleep
from datetime import datetime
from pprint import pprint

client = MongoClient(
    "mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["test"]
experts_collection = db["experts"]
users_collection = db["users"]
schedules_collection = db["schedules"]

