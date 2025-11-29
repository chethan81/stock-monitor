import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Simple database
def get_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create tables if they don't exist
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            email TEXT
        )
    ''')
    
    # Create admin user if not exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hashed_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)', 
                      ('admin', hashed_password, 'admin@stockmonitor.com'))
    
    conn.commit()
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

@app.route('/auth/register', methods=['POST'])
def auth_register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    # Validation
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('register'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('register'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if username already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        flash('Username already exists', 'error')
        conn.close()
        return redirect(url_for('register'))
    
    # Check if email already exists
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        flash('Email already registered', 'error')
        conn.close()
        return redirect(url_for('register'))
    
    # Create new user
    hashed_password = generate_password_hash(password)
    cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', 
                  (username, email, hashed_password))
    
    conn.commit()
    conn.close()
    
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('login'))

@app.route('/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    email = request.form['email']
    flash(f'Password reset link sent to {email} (Feature coming soon)', 'info')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', 
                         username=session.get('username', 'User'),
                         total_items=0,
                         current_stock_value=0,
                         expected_revenue=0,
                         recent_items=[])

@app.route('/items')
def items():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('items.html', items=[])

@app.route('/sales')
def sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('sales.html', sales=[], available_items=[])

@app.route('/wages')
def wages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('wages.html', wages=[], total_wages=0)

@app.route('/investment')
def investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('investment.html', 
                         total_invested=0,
                         stock_value=0,
                         transactions=[],
                         items=[])

@app.route('/investors')
def investors():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('investors.html', investors=[])

# Add all other routes
@app.route('/add_item')
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return "Add item feature coming soon!"

@app.route('/sell_item/<int:id>')
def sell_item(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return "Sell item feature coming soon!"

@app.route('/add_wage')
def add_wage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return "Add wage feature coming soon!"

@app.route('/investment/add')
def add_investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return "Add investment feature coming soon!"

@app.route('/investors/ledger/<name>')
def investor_ledger(name):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return "Investor ledger feature coming soon!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
