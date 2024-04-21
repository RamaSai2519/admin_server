# server/app.py
from flask import Flask, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from bson import ObjectId

app = Flask(__name__)
CORS(app)
client = MongoClient('mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['test']
blogs_collection = db['blogposts']
calls_collection = db['calls']
experts_collection = db['experts']
users_collection = db['users']

@app.route('/api/last-five-calls')
def get_last_five_calls():
    try:
        last_five_calls = list(calls_collection.find().sort([('initiatedTime', -1)]).limit(5))
        for call in last_five_calls:
            if 'user' in call:
                user = users_collection.find_one({'_id': call['user']})
                if user:
                    call['userName'] = user.get('name', 'Unknown')
                    call['user'] = str(call['user'])
                else:
                    call['userName'] = 'Unknown'
                    call['user'] = 'Unknown'
            else:
                call['userName'] = 'Unknown'
                call['user'] = 'Unknown'
            if 'expert' in call:
                expert = experts_collection.find_one({'_id': call['expert']})
                if expert:
                    call['expertName'] = expert.get('name', 'Unknown')
                    call['expert'] = str(call['expert'])
                else:
                    call['expertName'] = 'Unknown'
                    call['expert'] = 'Unknown'
            else:
                call['expertName'] = 'Unknown'
                call['expert'] = 'Unknown'
            call['_id'] = str(call.get('_id', ''))
        return jsonify(last_five_calls)
    except Exception as e:
        print('Error fetching last five calls:', e)
        return jsonify({'error': 'Failed to fetch last five calls'}), 500

from bson import ObjectId

@app.route('/api/all-calls')
def get_all_calls():
    try:
        # Fetch all calls with user and expert IDs
        pipeline = [
            {
                "$lookup": {
                    "from": "users_collection",
                    "localField": "user",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$lookup": {
                    "from": "experts_collection",
                    "localField": "expert",
                    "foreignField": "_id",
                    "as": "expert"
                }
            },
            {
                "$unset": ["Score Breakup", "Saarthi Feedback", "User Callback", "Summary"]
            }
        ]

        all_calls = list(calls_collection.aggregate(pipeline))

        # Prepare dictionary to map user IDs to their names
        user_map = {str(user['_id']): user.get('name', 'Unknown') for user in users_collection.find()}

        # Prepare dictionary to map expert IDs to their names
        expert_map = {str(expert['_id']): expert.get('name', 'Unknown') for expert in experts_collection.find()}

        # Update each call with user and expert names
        for call in all_calls:
            user_id = str(call.get('user', [{}])[0].get('_id')) if 'user' in call else 'Unknown'
            call['userName'] = user_map.get(user_id, 'Unknown')

            expert_id = str(call.get('expert', [{}])[0].get('_id')) if 'expert' in call else 'Unknown'
            call['expertName'] = expert_map.get(expert_id, 'Unknown')

            call['_id'] = str(call.get('_id', ''))

            # Clean up unnecessary fields
            call.pop('user', None)
            call.pop('expert', None)

        return jsonify(all_calls)
    except Exception as e:
        print('Error fetching all calls:', e)
        return jsonify({'error': 'Failed to fetch all calls'}), 500



@app.route('/api/online-saarthis')
def get_online_saarthis():
    online_saarthis = list(experts_collection.find({'status': 'online'}, {'categories': 0}))
    for saarthi in online_saarthis:
        saarthi['_id'] = str(saarthi.get('_id', ''))
    return jsonify(online_saarthis)

@app.route('/api/successful-calls')
def get_successful_calls():
    calls = list(calls_collection.find({}, {'_id': 0}))
    calls = list(filter(lambda call: call['status'] == 'successfull', calls))
    for call in calls:
        call['expert'] = str(call.get('expert', ''))
        call['user'] = str(call.get('user', ''))
    return jsonify(calls)

@app.route('/api/users')
def get_users():
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user.get('_id', ''))
    return jsonify(users)

@app.route('/api/experts')
def get_experts():
    experts = list(experts_collection.find({}, {'categories': 0}))
    for expert in experts:
        expert['_id'] = str(expert.get('_id', ''))
    return jsonify(experts)

@app.route('/api/calls')
def get_calls():
    calls = list(calls_collection.find({}, {'_id': 0}))
    for call in calls:
        call['expert'] = str(call.get('expert', ''))
        call['user'] = str(call.get('user', ''))
    return jsonify(calls)

@app.route('/api/experts/<string:id>')
def get_expert(id):
    expert = experts_collection.find_one({'_id': ObjectId(id)}, {'categories': 0})
    if expert:
        expert['_id'] = str(expert.get('_id', ''))
    print(expert.name)
    return jsonify(expert)

@app.route('/api/users/<string:id>')
def get_user(id):
    user = users_collection.find_one({'_id': ObjectId(id)})
    if user:
        user['_id'] = str(user.get('_id', ''))
    print(user.name)
    return jsonify(user)

@app.route('/api/calls/<string:id>')
def get_call(id):
    call = calls_collection.find_one({'callId': id})
    if 'user' in call:
        user = users_collection.find_one({'_id': call['user']})
        if user:
            call['userName'] = user.get('name', 'Unknown')
            call['user'] = str(call['user'])
        else:
            call['userName'] = 'Unknown'
            call['user'] = 'Unknown'
    else:
        call['userName'] = 'Unknown'
        call['user'] = 'Unknown'
    if 'expert' in call:
        expert = experts_collection.find_one({'_id': call['expert']})
        if expert:
            call['expertName'] = expert.get('name', 'Unknown')
            call['expert'] = str(call['expert'])
        else:
            call['expertName'] = 'Unknown'
            call['expert'] = 'Unknown'
    else:
        call['expertName'] = 'Unknown'
        call['expert'] = 'Unknown'
    call['_id'] = str(call.get('_id', ''))
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
