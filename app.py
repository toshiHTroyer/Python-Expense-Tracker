from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from dotenv import load_dotenv
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

#Load environment variables from .env file
load_dotenv()

#Initialize Flask app
app = Flask(__name__, template_folder='GUI')
app.secret_key = os.getenv("SECRET_KEY")

#Initalize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))
db = client["expense_tracker_db"]

#Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

#Load user
@login_manager.user_loader
def load_user(user_id):
    user = db.users.find_one({'_id': ObjectId(user_id)})
    return User(user['_id']) if user else None

# try:
#     client.admin.command("ping")
#     print(" *", "Connected to MongoDB!")
# except Exception as e:
#     print(" * MongoDB connection error:", e)

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.users.find_one({'username': username})
        if user and user['password'] == password:
            login_user(User(user['_id']))
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

expenseCollection = db.expenses

#Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if db.users.find_one({'username': username}):
            flash('Username already taken, please choose another', 'error')
        else:
            db.users.insert_one({'username': username, 'password': password})
            return redirect(url_for('login'))
    return render_template('register.html')

#Index
@app.route('/')
@login_required
def index():
    expenses = expenseCollection.find({'user_id': current_user.id}).sort('date', -1)
    return render_template('index.html', expenses=expenses)

#Creating a new expense
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        expense = {
            'date': datetime.datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'category': request.form['category'],
            'amount': float(request.form['amount']),
            'description': request.form['description'],
            'user_id': current_user.id
        }
        expenseCollection.insert_one(expense)
        return redirect(url_for('index'))
    return render_template('addExpense.html')

#Editing an existing expense
@app.route('/edit/<expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = expenseCollection.find_one({'_id': ObjectId(expense_id)})
    if request.method == 'POST':
        update = {
            'date': datetime.datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'category': request.form['category'],
            'amount': float(request.form['amount']),
            'description': request.form['description']
        }
        expenseCollection.update_one({'_id': ObjectId(expense_id)}, {'$set': update})
        return redirect(url_for('index'))
    return render_template('editExpense.html', expense=expense)

#Delete an existing expense
@app.route('/delete/<expense_id>', methods=['GET', 'POST'])
@login_required
def delete_expense(expense_id):
    expense = expenseCollection.find_one({'_id': ObjectId(expense_id)})
    if request.method == 'POST':
        expenseCollection.delete_one({'_id': ObjectId(expense_id)})
        return redirect(url_for('index'))
    
    return render_template('deleteExpense.html', expense=expense)
#Search for an expense
@app.route('/search', methods=['GET'])
@login_required
def search():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')

    query = {}
    error = None

    # Search by date range
    if start_date and end_date:
        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

            if start_date > end_date:
                error = "The start date must be earlier than or equal to the end date."
            else:
                query['date'] = {'$gte': start_date, '$lte': end_date}
        except ValueError:
            error = "Invalid date format. Please use YYYY-MM-DD."

    # Search by amount range
    if min_amount and max_amount:
        try:
            min_amount = float(min_amount)
            max_amount = float(max_amount)

            if min_amount > max_amount:
                error = "The minimum amount must be less than or equal to the maximum amount."
            else:
                query['amount'] = {'$gte': min_amount, '$lte': max_amount}
        except ValueError:
            error = "Please provide valid numbers for the amount range."

    # Check if any query was made (date range or amount range)
    if not (start_date or end_date or min_amount or max_amount):
        # Avoid showing error on page load when no search is performed
        return render_template('search.html', expenses=None, error=None)

    # Perform the search if there are no errors
    if error:
        return render_template('search.html', expenses=[], error=error)
   
    query.update({'user_id': current_user.id})
    
    expenses = list(expenseCollection.find(query).sort('date', 1))

    return render_template('search.html', expenses=expenses if expenses else [], error=error)

@app.route('/dashboard')
def dashboard():
    # Calculate total expenses
    total_expenses = expenseCollection.aggregate([
        {"$match": {'user_id': current_user.id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_expenses = total_expenses.next()["total"] if total_expenses.alive else 0

    # Calculate expenditure for the past 7 days
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    last_7_days_total = expenseCollection.aggregate([
        {"$match": {'user_id': current_user.id, "date": {"$gte": seven_days_ago}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    last_7_days_total = last_7_days_total.next()["total"] if last_7_days_total.alive else 0

    # Get the top 5 biggest spends
    top_5_expenses = list(expenseCollection.find({'user_id': current_user.id}).sort("amount", -1).limit(5))

    # Render the updated dashboard.html
    return render_template('dashboard.html',
                           total_expenses=total_expenses,
                           last_7_days_total=last_7_days_total,
                           top_5_expenses=top_5_expenses)

if __name__ == '__main__':
    app.run(debug=True)