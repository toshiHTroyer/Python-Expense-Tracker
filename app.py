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
@app.route('/delete/<expense_id>')
def delete_expense(expense_id):
    expenseCollection.delete_one({'_id': ObjectId(expense_id)})
    return redirect(url_for('index'))

#Search for an expense
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    
    #Validate the query
    if not query:
        return render_template('search.html', expenses=[], error="Please enter a search term.")
    
    #Perform the search
    expenses = expenseCollection.find({'$text': {'$search': query}})
    
    return render_template('search.html', expenses=expenses)

if __name__ == '__main__':
    app.run(debug=True)