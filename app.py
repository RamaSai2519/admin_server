# server/app.py
from flask import Flask, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from pprint import pprint

app = Flask(__name__)
CORS(app)
client = MongoClient('mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['test']
blogs_collection = db['blogposts']

@app.route('/api/blogs')
def get_blogs():
    blogs = list(blogs_collection.find({}, {'_id': 0}))
    pprint(blogs)
    return jsonify(blogs)

@app.route('/api/blogs/<string:id>', methods=['GET'])
def get_blog(id):
    blog = blogs_collection.find_one({'id': id})
    blog['_id'] = str(blog['_id'])
    return jsonify(blog)

@app.route('/api/featuredblog')
def get_featured_blog():
    featured_blog = blogs_collection.find_one(sort=[('id', -1)])
    featured_blog['_id'] = str(featured_blog['_id'])
    pprint(featured_blog)
    return jsonify(featured_blog)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80', debug=True)
