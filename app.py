# server/app.py
from flask import Flask, jsonify
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
client = MongoClient('mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['test']
blogs_collection = db['blogposts']
calls_collection = db['calls']
experts_collection = db['experts']

@app.route('/api/calls')
def get_calls():
    calls = list(calls_collection.find({}, {'_id': 0}))
    for call in calls:
        call['expert'] = str(call.get('expert', ''))
        call['user'] = str(call.get('user', ''))

    calls = jsonify(calls)
    return calls

@app.route('/api/experts')
def get_experts():
    experts = list(experts_collection.find({}, {'_id': 0}))
    for expert in experts:
        expert['_id'] = str(expert.get('_id'), '')
    return jsonify(experts)


@app.route('/api/calls/<string:id>')
def get_call(id):
    call = calls_collection.find_one({'callId': id})
    call['_id'] = str(call['_id'])
    call['expert'] = str(call.get('expert', ''))
    call['user'] = str(call.get('user', ''))
    return jsonify(call)

@app.route('/api/blogs')
def get_blogs():
    blogs = list(blogs_collection.find({}, {'_id': 0}))
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
    return jsonify(featured_blog)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80', debug=True)
