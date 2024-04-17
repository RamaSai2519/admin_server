from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB Atlas
client = MongoClient("mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["test"]
collection = db["calls"]

# Define the aggregation pipeline
pipeline = [
    {
        "$project": {
            "hourOfDay": {"$hour": {"$toDate": "$initiatedTime"}},
            "dayOfYear": {"$dayOfYear": {"$toDate": "$initiatedTime"}}
        }
    },
    {
        "$group": {
            "_id": {"dayOfYear": "$dayOfYear", "hourOfDay": "$hourOfDay"},
            "count": {"$sum": 1}
        }
    },
    {
        "$group": {
            "_id": "$_id.hourOfDay",
            "averageCalls": {"$avg": "$count"}
        }
    },
    {
        "$sort": {"_id": 1}
    }
]

# Execute the aggregation pipeline
result = collection.aggregate(pipeline)

# Define a function to convert 24-hour format to 12-hour format
# Define a function to convert 24-hour format to 12-hour format
def to_12_hour_format(hour):
    if hour is None:
        return "Unknown"
    if hour == 0:
        return "12am"
    elif hour < 12:
        return f"{hour}am"
    elif hour == 12:
        return "12pm"
    else:
        return f"{hour - 12}pm"

# Print the result
for doc in result:
    hour = to_12_hour_format(doc['_id'])
    print(f"{hour}: Average calls {doc['averageCalls']:.2f}")

# Close the MongoDB connection
client.close()
