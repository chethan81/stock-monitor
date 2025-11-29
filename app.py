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

# For Render, we need to use PostgreSQL instead of SQLite
# But for now, we'll keep SQLite for simplicity
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.getcwd(), 'database.db'))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    # Use fixed path for Render, local path for development
    db_path = '/opt/render/project/src/database.db'
    
    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError:
        # If the specific path doesn't work, try current directory
        conn = sqlite3.connect('database.db')
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
            password TEXT
        )
    ''')
    
    # Create stock_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            quantity INTEGER,
            initial_price REAL,
            selling_price REAL,
            description TEXT,
            image_path TEXT,
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
            sold_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT
        )
    ''')
    
    # Create investment_transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT,
            amount REAL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if admin user exists, if not create one
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hashed_password = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', hashed_password))
    
    conn.commit()
    conn.close()

# Initialize database on startup
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

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    email = request.form['email']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if email exists
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user:
        flash('If that email exists, a reset link has been sent.', 'info')
        conn.close()
        return redirect(url_for('login'))
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)
    
    # Store reset token
    cursor.execute('''
        INSERT INTO password_resets (email, token, expires_at)
        VALUES (?, ?, ?)
    ''', (email, token, expires_at))
    
    conn.commit()
    conn.close()
    
    # In production, you would send an email here
    # For demo, we'll show the token
    flash(f'Password reset token: {token} (In production, this would be emailed)', 'info')
    flash('Please copy this token and use it on the reset page.', 'info')
    
    return redirect(url_for('reset_password'))

@app.route('/reset-password')
def reset_password():
    return render_template('reset_password.html')

@app.route('/auth/reset-password', methods=['POST'])
def auth_reset_password():
    token = request.form['token']
    email = request.form['email']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('reset_password'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('reset_password'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if token is valid
    cursor.execute('''
        SELECT * FROM password_resets 
        WHERE email = ? AND token = ? AND expires_at > ? AND used = FALSE
        ORDER BY created_at DESC LIMIT 1
    ''', (email, token, datetime.now()))
    
    reset_request = cursor.fetchone()
    
    if not reset_request:
        flash('Invalid or expired token', 'error')
        conn.close()
        return redirect(url_for('reset_password'))
    
    # Update password
    hashed_password = generate_password_hash(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (hashed_password, email))
    
    # Mark token as used
    cursor.execute('UPDATE password_resets SET used = TRUE WHERE id = ?', (reset_request['id'],))
    
    conn.commit()
    conn.close()
    
    flash('Password reset successful! Please login.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
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

@app.route('/items')
@login_required
def items():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stock_items ORDER BY created_at DESC')
    items = cursor.fetchall()
    conn.close()
    return render_template('items.html', items=items)

@app.route('/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        selling_price = float(request.form['selling_price'])
        description = request.form['description']
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_path = file_path
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO stock_items (name, quantity, selling_price, description, image_path, total_initial_value, current_stock_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, quantity, selling_price, description, image_path, selling_price * quantity, selling_price * quantity))
        conn.commit()
        conn.close()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('items'))
    
    return render_template('add_item.html')

@app.route('/items/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        initial_price = float(request.form['initial_price'])
        selling_price = float(request.form['selling_price'])
        description = request.form['description']
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                # Get old image path to delete
                cursor.execute('SELECT image_path FROM stock_items WHERE id = ?', (id,))
                old_image = cursor.fetchone()
                if old_image and old_image['image_path']:
                    try:
                        os.remove(old_image['image_path'])
                    except:
                        pass
                
                # Save new image
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                cursor.execute('''
                    UPDATE stock_items 
                    SET name = ?, quantity = ?, initial_price = ?, selling_price = ?, description = ?, image_path = ?
                    WHERE id = ?
                ''', (name, quantity, initial_price, selling_price, description, file_path, id))
            else:
                cursor.execute('''
                    UPDATE stock_items 
                    SET name = ?, quantity = ?, initial_price = ?, selling_price = ?, description = ?
                    WHERE id = ?
                ''', (name, quantity, initial_price, selling_price, description, id))
        else:
            cursor.execute('''
                UPDATE stock_items 
                SET name = ?, quantity = ?, initial_price = ?, selling_price = ?, description = ?
                WHERE id = ?
            ''', (name, quantity, initial_price, selling_price, description, id))
        
        conn.commit()
        conn.close()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('items'))
    
    cursor.execute('SELECT * FROM stock_items WHERE id = ?', (id,))
    item = cursor.fetchone()
    conn.close()
    
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('items'))
    
    return render_template('edit_item.html', item=item)

@app.route('/items/delete/<int:id>')
@login_required
def delete_item(id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get image path to delete
    cursor.execute('SELECT image_path FROM stock_items WHERE id = ?', (id,))
    item = cursor.fetchone()
    
    if item and item['image_path']:
        try:
            os.remove(item['image_path'])
        except:
            pass
    
    cursor.execute('DELETE FROM stock_items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('items'))

@app.route('/items/sell/<int:id>', methods=['GET', 'POST'])
@login_required
def sell_item(id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM stock_items WHERE id = ?', (id,))
    item = cursor.fetchone()
    
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('items'))
    
    if request.method == 'POST':
        quantity_sold = int(request.form['quantity_sold'])
        place = request.form['place']
        
        if quantity_sold > item['quantity']:
            flash('Cannot sell more than available quantity', 'error')
            return render_template('sell_item.html', item=item)
        
        # Handle sale image upload
        sale_image_path = None
        image_data = request.form.get('imageData')
        
        if image_data and image_data.startswith('data:image'):
            # Handle base64 image data from camera
            import base64
            from io import BytesIO
            
            # Extract the base64 data
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            
            # Generate filename and save
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sale_{timestamp}_camera.jpg"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            sale_image_path = file_path
        elif 'sale_image' in request.files:
            # Handle traditional file upload
            file = request.files['sale_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"sale_{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                sale_image_path = file_path
        
        # Update stock quantity and current stock value
        new_quantity = item['quantity'] - quantity_sold
        new_current_value = new_quantity * item['selling_price']
        cursor.execute('UPDATE stock_items SET quantity = ?, current_stock_value = ? WHERE id = ?', (new_quantity, new_current_value, id))
        
        # Add to sales
        total_amount = quantity_sold * item['selling_price']
        cursor.execute('''
            INSERT INTO sales (item_id, item_name, quantity_sold, selling_price, total_amount, image_path, sale_image_path, user_id, user_name, user_email, place)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id, item['name'], quantity_sold, item['selling_price'], total_amount, item['image_path'], sale_image_path, 
              session['user_id'], session['username'], session['user_email'] if 'user_email' in session else '', place))
        
        conn.commit()
        conn.close()
        
        flash(f'Item sold successfully! {quantity_sold} units sold.', 'success')
        return redirect(url_for('sales'))
    
    conn.close()
    return render_template('sell_item.html', item=item)

@app.route('/sales')
@login_required
def sales():
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

@app.route('/investment')
@login_required
def investment():
    # Check if user is admin
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
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

@app.route('/investment/add', methods=['GET', 'POST'])
@login_required
def add_investment():
    # Check if user is admin
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        transaction_type = request.form['transaction_type']
        amount = float(request.form['amount'])
        description = request.form['description']
        investor_name = request.form['investor_name']
        investor_email = request.form['investor_email']
        investor_phone = request.form['investor_phone']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO investment_transactions (transaction_type, amount, description, investor_name, investor_email, investor_phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (transaction_type, amount, description, investor_name, investor_email, investor_phone))
        conn.commit()
        conn.close()
        
        flash(f'{transaction_type.title()} of ${amount:.2f} from {investor_name} recorded successfully!', 'success')
        return redirect(url_for('investment'))
    
    return render_template('add_investment.html')

@app.route('/wages')
@login_required
def wages():
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

@app.route('/wages/add', methods=['GET', 'POST'])
@login_required
def add_wage():
    if request.method == 'POST':
        employee_name = request.form['employee_name']
        amount = float(request.form['amount'])
        wage_type = request.form['wage_type']
        description = request.form['description']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO wages (employee_name, amount, wage_type, description)
            VALUES (?, ?, ?, ?)
        ''', (employee_name, amount, wage_type, description))
        conn.commit()
        conn.close()
        
        flash(f'Wage payment of ${amount:.2f} to {employee_name} recorded successfully!', 'success')
        return redirect(url_for('wages'))
    
    return render_template('add_wage.html')

@app.route('/wages/delete/<int:id>')
@login_required
def delete_wage(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wages WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Wage record deleted successfully!', 'success')
    return redirect(url_for('wages'))

@app.route('/investors/ledger/<name>')
@login_required
def investor_ledger(name):
    # Check if user is admin
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM investment_transactions 
        WHERE investor_name = ? 
        ORDER BY created_at DESC
    ''', (name,))
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

@app.route('/investors')
@login_required
def investors():
    # Check if user is admin
    if session.get('username') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
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

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    init_db()
    
    # Ensure upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Run on port specified by Render or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
