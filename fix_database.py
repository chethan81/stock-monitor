import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import secrets
import base64
from functools import wraps

app = Flask(__name__)

# Configuration for Render
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Use PostgreSQL on Render
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    
    def query_db(query, args=(), one=False):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, args)
        if one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        conn.close()
        return result
    
    def execute_db(query, args=()):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        conn.close()
    
else:
    # Use SQLite for local development
    DATABASE_PATH = 'database.db'
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def get_db():
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def query_db(query, args=(), one=False):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, args)
        if one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        conn.close()
        return result
    
    def execute_db(query, args=()):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        conn.close()

def init_db():
    if DATABASE_URL:
        # PostgreSQL setup
        execute_db('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100),
                password_hash VARCHAR(255),
                profile_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        execute_db('''
            CREATE TABLE IF NOT EXISTS stock_items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                quantity INTEGER NOT NULL,
                selling_price REAL NOT NULL,
                description TEXT,
                image_path TEXT,
                total_initial_value REAL,
                current_stock_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        execute_db('''
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                item_id INTEGER,
                item_name VARCHAR(100),
                quantity_sold INTEGER,
                selling_price REAL,
                total_amount REAL,
                image_path TEXT,
                sale_image_path TEXT,
                user_id INTEGER,
                user_name VARCHAR(50),
                user_email VARCHAR(100),
                place VARCHAR(100),
                sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if admin user exists
        admin = query_db('SELECT * FROM users WHERE username = %s', ('admin',), one=True)
        if not admin:
            hashed_password = generate_password_hash('admin123')
            execute_db('INSERT INTO users (username, password_hash) VALUES (%s, %s)', ('admin', hashed_password))
    else:
        # SQLite setup
        execute_db('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT,
                password_hash TEXT,
                profile_image TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        execute_db('''
            CREATE TABLE IF NOT EXISTS stock_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                selling_price REAL NOT NULL,
                description TEXT,
                image_path TEXT,
                total_initial_value REAL,
                current_stock_value REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        execute_db('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                item_name TEXT,
                quantity_sold INTEGER,
                selling_price REAL,
                total_amount REAL,
                image_path TEXT,
                sale_image_path TEXT,
                user_id INTEGER,
                user_name TEXT,
                user_email TEXT,
                place TEXT,
                sold_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if admin user exists
        admin = query_db('SELECT * FROM users WHERE username = ?', ('admin',), one=True)
        if not admin:
            hashed_password = generate_password_hash('admin123')
            execute_db('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', hashed_password))

# Initialize database
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
    
    if DATABASE_URL:
        user = query_db('SELECT * FROM users WHERE username = %s', (username,), one=True)
        password_valid = user and check_password_hash(user['password_hash'], password)
    else:
        user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
        password_valid = user and check_password_hash(user['password_hash'], password)
    
    if password_valid:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['user_email'] = user.get('email', '')
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if DATABASE_URL:
        total_items = query_db('SELECT COUNT(*) as count FROM stock_items', one=True)['count']
        current_stock_value = query_db('SELECT SUM(current_stock_value) as total FROM stock_items', one=True)['total'] or 0
        expected_revenue = query_db('SELECT SUM(selling_price * quantity) as total FROM stock_items', one=True)['total'] or 0
        recent_items = query_db('SELECT * FROM stock_items ORDER BY created_at DESC LIMIT 5')
    else:
        total_items = query_db('SELECT COUNT(*) as count FROM stock_items', one=True)['count']
        current_stock_value = query_db('SELECT SUM(current_stock_value) as total FROM stock_items', one=True)['total'] or 0
        expected_revenue = query_db('SELECT SUM(selling_price * quantity) as total FROM stock_items', one=True)['total'] or 0
        recent_items = query_db('SELECT * FROM stock_items ORDER BY created_at DESC LIMIT 5')
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         total_items=total_items,
                         current_stock_value=current_stock_value,
                         expected_revenue=expected_revenue,
                         recent_items=recent_items)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
