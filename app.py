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
@app.route('/api/delete_food_log', methods=['POST'])
def delete_food_log():
    log_id = request.json.get('log_id')
    
    if not log_id:
        return jsonify({'error': 'No log_id provided'}), 400
    
    result = db.food_logs.delete_one({'_id': ObjectId(log_id)})
    
    if result.deleted_count == 1:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete log'}), 500
    
@app.route('/api/get_daily_calories', methods=['GET'])
def get_daily_calories():
    user_id = request.args.get('user_id')
    date_str = request.args.get('date')
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

    # Lấy tất cả food logs của user trong ngày đã chọn
    food_logs = list(db.food_logs.find({
        'user_id': ObjectId(user_id),
        'date': date
    }))

    # Tính tổng lượng calo
    total_calories = 0
    for log in food_logs:
        total_calories += (log['quantity'] * log['calories']) / log['unit']

    # Định dạng dữ liệu trả về, bao gồm log_id và ngày định dạng "ngày-tháng-năm"
    response_data = {
        'total_calories': total_calories,
        'food_logs': [{
            'log_id': str(log['_id']),  # Chuyển ObjectId thành string
            'food': log['food'],
            'quantity': log['quantity'],
            'unit': log['number-gam'],
            'calories': log['calories'],
            'date': log['date'].strftime('%d-%m-%Y')  # Định dạng ngày "ngày-tháng-năm"
        } for log in food_logs]
    }

    return jsonify(response_data)



if __name__ == '__main__':
    app.run(debug=True)
