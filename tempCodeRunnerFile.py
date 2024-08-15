from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

app = Flask(__name__)

# Kết nối với MongoDB
client = MongoClient('mongodb+srv://datpy:lydat123456789@cluster0.i2hz1.mongodb.net/CalorieTrackerDB')
db = client['calorie_tracker']

# Trang chủ
@app.route('/')
def index():
    return render_template('index.html')

# Trang đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        user = {
            'name': data['name'],
            'email': data['email'],
            'password': data['password']
        }
        db.users.insert_one(user)
        return redirect(url_for('login'))
    return render_template('register.html')

# # Trang đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        user = db.users.find_one({'email': data['email'], 'password': data['password']})
        if user:
            return redirect(url_for('dashboard', user_id=str(user['_id'])))
        return 'Invalid email or password', 401
    return render_template('login.html')

# Trang bảng điều khiển
@app.route('/dashboard/<user_id>', methods=['GET', 'POST'])
def dashboard(user_id):
    if request.method == 'POST':
        data = request.form
        if (data['number-gam'] == "number"):
            unit=1
        else:
            unit=100
        food_log = {
            'user_id': ObjectId(user_id),
            'food': data['food'],
            'quantity': float(data['quantity']),
            'number-gam' : data['number-gam'],
            'calories': float(data['calories']),
            'date': datetime.datetime.strptime(data['date'], '%Y-%m-%d'),
            'unit' : unit
        }
        db.food_logs.insert_one(food_log)
    foods = list(db.foods.find())
    return render_template('dashboard.html', user_id=user_id, foods=foods)

# API lấy tổng lượng calo
@app.route('/api/get_daily_calories', methods=['GET'])
def get_daily_calories():
    user_id = request.args.get('user_id')
    date_str = request.args.get('date')
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

    pipeline = [
        {
            '$match': {
                'user_id': ObjectId(user_id),
                'date': date
            }
        },
        {
            '$project': {
                'total_calories': {
                    '$divide': [
                    {'$multiply': ['$quantity', '$calories']}, '$unit' ]
                     
                }
            }
        },
        {
            '$group': {
                '_id': '$user_id',
                'total_calories': {'$sum': '$total_calories'}
            }
        }
    ]

    result = list(db.food_logs.aggregate(pipeline))
    if result:
        total_calories = result[0]['total_calories']
    else:
        total_calories = 0

    return jsonify({'date': date_str, 'total_calories': total_calories})

if __name__ == '__main__':
    app.run(debug=True)