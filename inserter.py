from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient(
    "mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["test"]
users_collection = db["users"]

users = list(users_collection.find())
