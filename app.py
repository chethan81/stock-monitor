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
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database configuration - use SQLite with proper path handling
def get_db():
    # Try multiple paths for Render compatibility
    paths = [
        '/opt/render/project/src/database.db',
        'database.db',
        os.path.join(os.getcwd(), 'database.db')
    ]
    
    for path in paths:
        try:
            # Ensure directory exists
            db_dir = os.path.dirname(path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError:
            continue
    
    # If all paths fail, create database in memory
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    return conn

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password_hash TEXT,
            profile_image TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create stock_items table
    cursor.execute('''
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
    
    # Create sales table
    cursor.execute('''
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
    
    # Create investment_transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT,
            amount REAL,
            description TEXT,
            investor_name TEXT,
            investor_email TEXT,
            investor_phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create wages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT,
            amount REAL,
            wage_type TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create password_resets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            token TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if admin user exists, if not create one
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hashed_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', hashed_password))
    
    conn.commit()
    conn.close()

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"Database initialization error: {e}")

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
    try:
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        # Check both password_hash and password columns for compatibility
        password_valid = False
        if user:
            if 'password_hash' in user.keys() and user['password_hash']:
                password_valid = check_password_hash(user['password_hash'], password)
            elif 'password' in user.keys() and user['password']:
                password_valid = check_password_hash(user['password'], password)
        
        if password_valid:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_email'] = user['email'] if 'email' in user.keys() and user['email'] else ''
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

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/auth/register', methods=['POST'])
def auth_register():
    try:
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
        
        # Handle profile image
        profile_image = None
        image_data = request.form.get('imageData')
        
        if image_data and image_data.startswith('data:image'):
            # Handle base64 image data from camera
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            
            # Generate filename and save
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"profile_{timestamp}_camera.jpg"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure upload directory exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            profile_image = file_path
        elif 'profile_image' in request.files:
            # Handle traditional file upload
            file = request.files['profile_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"profile_{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Ensure upload directory exists
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                file.save(file_path)
                profile_image = file_path
        
        # Create new user
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, profile_image, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, hashed_password, profile_image, datetime.now()))
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'error')
        return redirect(url_for('register'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total items
        cursor.execute('SELECT COUNT(*) as count FROM stock_items')
        total_items = cursor.fetchone()['count']
        
        # Get current stock value
        cursor.execute('SELECT SUM(current_stock_value) as total FROM stock_items')
        current_stock_value = cursor.fetchone()['total'] or 0
        
        # Get expected revenue (based on selling price of current stock)
        cursor.execute('SELECT SUM(selling_price * quantity) as total FROM stock_items')
        expected_revenue = cursor.fetchone()['total'] or 0
        
        # Get recent items
        cursor.execute('SELECT * FROM stock_items ORDER BY created_at DESC LIMIT 5')
        recent_items = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', 
                             username=session['username'],
                             total_items=total_items,
                             current_stock_value=current_stock_value,
                             expected_revenue=expected_revenue,
                             recent_items=recent_items)
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return render_template('dashboard.html', username=session['username'], total_items=0, current_stock_value=0, expected_revenue=0, recent_items=[])

@app.route('/items')
@login_required
def items():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stock_items ORDER BY created_at DESC')
        items_list = cursor.fetchall()
        conn.close()
        return render_template('items.html', items=items_list)
    except Exception as e:
        flash(f'Items error: {str(e)}', 'error')
        return render_template('items.html', items=[])

@app.route('/sales')
@login_required
def sales():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all sales
        cursor.execute('SELECT * FROM sales ORDER BY sold_at DESC')
        sales_list = cursor.fetchall()
        
        # Get available items for sale
        cursor.execute('SELECT * FROM stock_items WHERE quantity > 0 ORDER BY name')
        available_items = cursor.fetchall()
        
        conn.close()
        return render_template('sales.html', sales=sales_list, available_items=available_items)
    except Exception as e:
        flash(f'Sales error: {str(e)}', 'error')
        return render_template('sales.html', sales=[], available_items=[])

@app.route('/wages')
@login_required
def wages():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total wages paid
        cursor.execute('SELECT SUM(amount) as total FROM wages')
        total_wages = cursor.fetchone()['total'] or 0
        
        # Get all wages
        cursor.execute('SELECT * FROM wages ORDER BY created_at DESC')
        wages_list = cursor.fetchall()
        
        conn.close()
        return render_template('wages.html', wages=wages_list, total_wages=total_wages)
    except Exception as e:
        flash(f'Wages error: {str(e)}', 'error')
        return render_template('wages.html', wages=[], total_wages=0)

@app.route('/investment')
@login_required
def investment():
    # Check if user is admin
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total investment from transactions
        cursor.execute('SELECT SUM(CASE WHEN transaction_type = "invest" THEN amount ELSE -amount END) as total FROM investment_transactions')
        total_invested = cursor.fetchone()['total'] or 0
        
        # Get stock value
        cursor.execute('SELECT SUM(current_stock_value) as total FROM stock_items')
        stock_value = cursor.fetchone()['total'] or 0
        
        # Get all transactions
        cursor.execute('SELECT * FROM investment_transactions ORDER BY created_at DESC')
        transactions = cursor.fetchall()
        
        # Get items list
        cursor.execute('SELECT * FROM stock_items ORDER BY name')
        items_list = cursor.fetchall()
        
        conn.close()
        
        return render_template('investment.html', 
                             total_invested=total_invested,
                             stock_value=stock_value,
                             transactions=transactions,
                             items=items_list)
    except Exception as e:
        flash(f'Investment error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/investors')
@login_required
def investors():
    # Check if user is admin
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT investor_name, investor_email, investor_phone, transaction_type, amount
            FROM investment_transactions
        ''')
        transactions = cursor.fetchall()
        conn.close()
        
        investor_data = {}
        for t in transactions:
            name, email, phone, type, amount = t
            if name not in investor_data:
                investor_data[name] = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'total_invested': 0.0,
                    'total_withdrawn': 0.0,
                    'balance': 0.0
                }
            
            if type == 'invest':
                investor_data[name]['total_invested'] += amount
            else:
                investor_data[name]['total_withdrawn'] += amount
            
            investor_data[name]['balance'] = investor_data[name]['total_invested'] - investor_data[name]['total_withdrawn']
                
        investors_list = list(investor_data.values())
        
        return render_template('investors.html', investors=investors_list)
    except Exception as e:
        flash(f'Investors error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    init_db()
    
    # Ensure upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Run on port specified by Render or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
