import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Simple in-memory database for Render compatibility
def get_db():
    try:
        # Try to create a persistent database
        conn = sqlite3.connect('/tmp/database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except:
        # Fallback to in-memory database
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            email TEXT,
            created_at TEXT
        )
    ''')
    
    # Create admin user if not exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hashed_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)', 
                      ('admin', hashed_password, 'admin@stockmonitor.com', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    username = request.form['username']
    password = request.form['password']
    
    try:
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
    except Exception as e:
        flash(f'Login error: {str(e)}', 'error')
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
