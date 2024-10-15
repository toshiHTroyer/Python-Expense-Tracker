from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from dotenv import load_dotenv
import os

#Load environment variables from .env file
load_dotenv() 

#Initialize Flask app
app = Flask(__name__, template_folder='GUI')

#Initalize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))   
db = client["expense_tracker_db"]

# try:
#     client.admin.command("ping")
#     print(" *", "Connected to MongoDB!")
# except Exception as e:
#     print(" * MongoDB connection error:", e)

expenseCollection = db.expenses

@app.route('/')
def index():
    expenses = expenseCollection.find().sort('date', -1)
    return render_template('index.html', expenses=expenses)

#Creating a new expense
@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        expense = {
            'date': datetime.datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'category': request.form['category'],
            'amount': float(request.form['amount']),
            'description': request.form['description']
        }
        expenseCollection.insert_one(expense)
        return redirect(url_for('index'))
    return render_template('addExpense.html')

#Editing an existing expense
@app.route('/edit/<expense_id>', methods=['GET', 'POST'])
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
def delete_expense(expense_id):
    expense = expenseCollection.find_one({'_id': ObjectId(expense_id)})
    if request.method == 'POST':
        expenseCollection.delete_one({'_id': ObjectId(expense_id)})
        return redirect(url_for('index'))
    
    return render_template('deleteExpense.html', expense=expense)
#Search for an expense
@app.route('/search', methods=['GET'])
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

    # Query MongoDB and convert the cursor to a list
    expenses = list(expenseCollection.find(query).sort('date', 1))

    # If no expenses found, still pass an empty list to the template
    return render_template('search.html', expenses=expenses if expenses else [], error=error)

if __name__ == '__main__':
    app.run(debug=True)