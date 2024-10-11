from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import datetime

app = Flask(__name__)
client = MongoClient('mongodb:// ??????')   # ADJUST URI FOR MongoDB SETUP
                                            # FIX LATER

db = client['expense_tracker']
expenseCollection = db.expenses

@app.route('/')
def index():
    expenses = expenseCollection.find().sort('date', -1)
    return render_template('index.html', expenses=expenses)

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
    return render_template('add_expense.html')

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
    return render_template('edit_expense.html', expense=expense)

@app.route('/delete/<expense_id>')
def delete_expense(expense_id):
    expenseCollection.delete_one({'_id': ObjectId(expense_id)})
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    expenses = expenseCollection.find({'$text': {'$search': query}})
    return render_template('search_results.html', expenses=expenses)

if __name__ == '__main__':
    app.run(debug=True)