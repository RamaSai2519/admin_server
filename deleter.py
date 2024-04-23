from pymongo import MongoClient

# Connect to the MongoDB cluster
client = MongoClient('mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

# Access the 'test' database
db = client['test']

# Define the array of city names to replace
city_names_to_replace = ["Pune", "Pune "]

# Define the new city name
new_city_name = "Pune"

# Update documents where the city is in the list of city_names_to_replace
result = db.users.update_many(
    {"city": {"$in": city_names_to_replace}},
    {"$set": {"city": new_city_name}}
)

# Optionally, you can print updated documents to verify
updated_documents = db.users.find({"city": new_city_name})
