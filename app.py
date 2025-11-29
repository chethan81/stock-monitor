import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Global database connection for persistence
DATABASE_FILE = '/tmp/stock_monitor.db'

def init_database():
    """Initialize database with tables and admin user"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create stock items table
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
            user_id INTEGER,
            user_name TEXT,
            user_email TEXT,
            place TEXT,
            sold_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create investment transactions table
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
    
    # Check if admin user exists, if not create it
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    admin_user = cursor.fetchone()
    
    if not admin_user:
        print("Creating admin user...")
        hashed_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)', 
                      ('admin', hashed_password, 'admin@stockmonitor.com'))
        
        # Verify admin user was created
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        admin_check = cursor.fetchone()
        if admin_check:
            print(f"Admin user created successfully: {admin_check['username']}")
        else:
            print("ERROR: Failed to create admin user")
    else:
        print(f"Admin user already exists: {admin_user['username']}")
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database on startup
init_database()

@app.route('/')
def index():
    return "Stock Monitor App is Running! <a href='/login'>Go to Login</a>"

@app.route('/test')
def test():
    return "Test route working! <a href='/login'>Go to Login</a>"

@app.route('/debug/users')
def debug_users():
    """Debug route to check existing users"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, created_at FROM users')
        users = cursor.fetchall()
        conn.close()
        
        user_list = "<h2>Existing Users:</h2><ul>"
        for user in users:
            user_list += f"<li>ID: {user['id']}, Username: {user['username']}, Email: {user['email']}</li>"
        user_list += "</ul>"
        
        return user_list
    except Exception as e:
        return f"Error: {str(e)}"

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
    try:
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
            session['user_email'] = user['email'] if user['email'] else ''
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    except Exception as e:
        flash(f'Login error: {str(e)}', 'error')
        return redirect(url_for('login'))

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
        
        # Create new user
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', 
                      (username, email, hashed_password))
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'error')
        return redirect(url_for('register'))

@app.route('/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    email = request.form['email']
    flash(f'Password reset instructions sent to {email}', 'info')
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
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total items
        cursor.execute('SELECT COUNT(*) as count FROM stock_items')
        total_items = cursor.fetchone()['count']
        
        # Get current stock value
        cursor.execute('SELECT SUM(current_stock_value) as total FROM stock_items')
        current_stock_value = cursor.fetchone()['total'] or 0
        
        # Get expected revenue
        cursor.execute('SELECT SUM(selling_price * quantity) as total FROM stock_items')
        expected_revenue = cursor.fetchone()['total'] or 0
        
        # Get recent items
        cursor.execute('SELECT * FROM stock_items ORDER BY created_at DESC LIMIT 5')
        recent_items = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', 
                             username=session['username'] if 'username' in session else 'User',
                             total_items=total_items,
                             current_stock_value=current_stock_value,
                             expected_revenue=expected_revenue,
                             recent_items=recent_items)
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return render_template('dashboard.html', 
                             username=session['username'] if 'username' in session else 'User',
                             total_items=0, current_stock_value=0, 
                             expected_revenue=0, recent_items=[])

@app.route('/items')
def items():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            quantity = int(request.form['quantity'])
            selling_price = float(request.form['selling_price'])
            description = request.form.get('description', '')
            
            # Calculate values
            total_initial_value = quantity * selling_price
            current_stock_value = quantity * selling_price
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO stock_items (name, quantity, selling_price, description, 
                                       total_initial_value, current_stock_value)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, quantity, selling_price, description, 
                  total_initial_value, current_stock_value))
            conn.commit()
            conn.close()
            
            flash('Item added successfully!', 'success')
            return redirect(url_for('items'))
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
            return redirect(url_for('add_item'))
    
    return render_template('add_item.html')

@app.route('/sales')
def sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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

@app.route('/sell_item/<int:id>', methods=['GET', 'POST'])
def sell_item(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get item details
    cursor.execute('SELECT * FROM stock_items WHERE id = ?', (id,))
    item = cursor.fetchone()
    
    if not item:
        flash('Item not found', 'error')
        conn.close()
        return redirect(url_for('sales'))
    
    if request.method == 'POST':
        try:
            quantity_sold = int(request.form['quantity_sold'])
            place = request.form.get('place', '')
            
            if quantity_sold > item['quantity']:
                flash('Not enough stock available', 'error')
                conn.close()
                return redirect(url_for('sell_item', id=id))
            
            # Update item quantity
            new_quantity = item['quantity'] - quantity_sold
            cursor.execute('UPDATE stock_items SET quantity = ?, current_stock_value = ? WHERE id = ?', 
                          (new_quantity, new_quantity * item['selling_price'], id))
            
            # Add to sales
            total_amount = quantity_sold * item['selling_price']
            cursor.execute('''
                INSERT INTO sales (item_id, item_name, quantity_sold, selling_price, total_amount, 
                                 image_path, user_id, user_name, user_email, place)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id, item['name'], quantity_sold, item['selling_price'], total_amount, 
                  item['image_path'], session['user_id'], session['username'], 
                  session['user_email'] if 'user_email' in session else '', place))
            
            conn.commit()
            flash(f'Sold {quantity_sold} {item["name"]} successfully!', 'success')
            return redirect(url_for('sales'))
        except Exception as e:
            flash(f'Error selling item: {str(e)}', 'error')
    
    conn.close()
    return render_template('sell_item.html', item=item)

@app.route('/wages')
def wages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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

@app.route('/add_wage', methods=['GET', 'POST'])
def add_wage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            employee_name = request.form['employee_name']
            amount = float(request.form['amount'])
            wage_type = request.form['wage_type']
            description = request.form.get('description', '')
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO wages (employee_name, amount, wage_type, description) VALUES (?, ?, ?, ?)', 
                          (employee_name, amount, wage_type, description))
            conn.commit()
            conn.close()
            
            flash('Wage added successfully!', 'success')
            return redirect(url_for('wages'))
        except Exception as e:
            flash(f'Error adding wage: {str(e)}', 'error')
    
    return render_template('add_wage.html')

@app.route('/investment')
def investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total investment
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

@app.route('/investment/add', methods=['GET', 'POST'])
def add_investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            transaction_type = request.form['transaction_type']
            amount = float(request.form['amount'])
            description = request.form['description']
            investor_name = request.form['investor_name']
            investor_email = request.form['investor_email']
            investor_phone = request.form['investor_phone']
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO investment_transactions (transaction_type, amount, description, 
                                                 investor_name, investor_email, investor_phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_type, amount, description, investor_name, investor_email, investor_phone))
            conn.commit()
            conn.close()
            
            flash(f'{transaction_type.title()} of ${amount:.2f} from {investor_name} recorded successfully!', 'success')
            return redirect(url_for('investment'))
        except Exception as e:
            flash(f'Error adding investment: {str(e)}', 'error')
    
    return render_template('add_investment.html')

@app.route('/investors')
def investors():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT investor_name, investor_email, investor_phone, transaction_type, amount FROM investment_transactions')
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

@app.route('/investors/ledger/<name>')
def investor_ledger(name):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM investment_transactions WHERE investor_name = ? ORDER BY created_at DESC', (name,))
        transactions = cursor.fetchall()
        
        # Calculate totals
        total_invested = sum(t['amount'] for t in transactions if t['transaction_type'] == 'invest')
        total_withdrawn = sum(t['amount'] for t in transactions if t['transaction_type'] == 'withdraw')
        balance = total_invested - total_withdrawn
        
        conn.close()
        
        return render_template('investor_ledger.html', 
                             investor_name=name, 
                             transactions=transactions,
                             total_invested=total_invested,
                             total_withdrawn=total_withdrawn,
                             balance=balance)
    except Exception as e:
        flash(f'Investor ledger error: {str(e)}', 'error')
        return redirect(url_for('investors'))

if __name__ == '__main__':
    # Ensure upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
