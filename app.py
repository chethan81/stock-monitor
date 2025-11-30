import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import execute_query, init_database, test_connection
# MySQL deployment fix - v3 - env vars updated

app = Flask(__name__)
print("Flask app created successfully")
# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize database on startup (skip for now to get app running)
# try:
#     print("Starting database initialization...")
#     init_database()
#     print("Database initialized successfully")
# except Exception as e:
#     print(f"Database initialization failed: {e}")
#     # Continue without database for debugging

def format_currency(amount):
    """Format amount with rupee symbol"""
    return f"₹{amount:,.2f}"

def get_db():
    """Get database connection (legacy function for compatibility)"""
    # This function is kept for backward compatibility
    # All actual database operations should use execute_query from database.py
    return None

@app.route('/test-db')
def test_db():
    """Test database connection endpoint"""
    try:
        result = test_connection()
        return {"status": "success", "connection": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def index():
    return "Stock Monitor App is Running! <a href='/login'>Go to Login</a>"

@app.route('/test')
def test():
    return "Test route working! <a href='/login'>Go to Login</a>"

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
        
        user = execute_query(
            'SELECT * FROM users WHERE username = %s', 
            (username,), 
            fetch_one=True
        )
        
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
        
        try:
            # Check if username already exists
            existing_user = execute_query(
                'SELECT * FROM users WHERE username = %s', 
                (username,), 
                fetch_one=True
            )
            if existing_user:
                flash('Username already exists', 'error')
                return redirect(url_for('register'))
            
            # Check if email already exists
            existing_email = execute_query(
                'SELECT * FROM users WHERE email = %s', 
                (email,), 
                fetch_one=True
            )
            if existing_email:
                flash('Email already registered', 'error')
                return redirect(url_for('register'))
            
            # Create new user
            hashed_password = generate_password_hash(password)
            execute_query(
                'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)', 
                (username, email, hashed_password)
            )
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as db_error:
            flash(f'Database error: {str(db_error)}', 'error')
            return redirect(url_for('register'))
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
        # Get total items
        total_items_result = execute_query('SELECT COUNT(*) as count FROM stock_items', fetch_one=True)
        total_items = total_items_result['count'] if total_items_result else 0
        
        # Get current stock value
        stock_value_result = execute_query('SELECT SUM(current_stock_value) as total FROM stock_items', fetch_one=True)
        current_stock_value = stock_value_result['total'] or 0
        
        # Get expected revenue
        revenue_result = execute_query('SELECT SUM(selling_price * quantity) as total FROM stock_items', fetch_one=True)
        expected_revenue = revenue_result['total'] or 0
        
        # Get recent items
        recent_items = execute_query('SELECT * FROM stock_items ORDER BY created_at DESC LIMIT 5', fetch_all=True)
        
        return render_template('dashboard.html', 
                             username=session['username'] if 'username' in session else 'User',
                             total_items=total_items,
                             current_stock_value=current_stock_value,
                             expected_revenue=expected_revenue,
                             recent_items=recent_items or [])
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
        items_list = execute_query('''
            SELECT si.*, u.username as added_by_username 
            FROM stock_items si 
            LEFT JOIN users u ON si.added_by = u.id 
            ORDER BY si.created_at DESC
        ''', fetch_all=True)
        return render_template('items.html', items=items_list or [])
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
            
            # Calculate initial price (admin only)
            initial_price = 0.0
            if session.get('username') == 'admin':
                initial_price = float(request.form.get('initial_price', 0.0))
            
            # Calculate values
            total_initial_value = quantity * initial_price if initial_price > 0 else quantity * selling_price
            current_stock_value = quantity * selling_price
            
            execute_query('''
                INSERT INTO stock_items (name, quantity, selling_price, description, 
                                       total_initial_value, current_stock_value, initial_price, added_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, quantity, selling_price, description, 
                  total_initial_value, current_stock_value, initial_price, session['user_id']))
            
            flash('Item added successfully!', 'success')
            return redirect(url_for('items'))
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
            return redirect(url_for('add_item'))
    
    return render_template('add_item.html', is_admin=session.get('username') == 'admin')

@app.route('/edit_item/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get item details
    item = execute_query('SELECT * FROM stock_items WHERE id = %s', (id,), fetch_one=True)
    
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('items'))
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            quantity = int(request.form['quantity'])
            selling_price = float(request.form['selling_price'])
            description = request.form.get('description', '')
            
            # Calculate initial price (admin only)
            initial_price = item.get('initial_price', 0.0)
            if session.get('username') == 'admin':
                initial_price = float(request.form.get('initial_price', initial_price))
            
            # Calculate values
            total_initial_value = quantity * initial_price if initial_price > 0 else quantity * selling_price
            current_stock_value = quantity * selling_price
            
            execute_query('UPDATE stock_items SET name = %s, quantity = %s, selling_price = %s, description = %s, total_initial_value = %s, current_stock_value = %s, initial_price = %s WHERE id = %s', 
                          (name, quantity, selling_price, description, total_initial_value, current_stock_value, initial_price, id))
            
            flash('Item updated successfully!', 'success')
            return redirect(url_for('items'))
        except Exception as e:
            flash(f'Error updating item: {str(e)}', 'error')
            return redirect(url_for('edit_item', id=id))
    
    return render_template('edit_item.html', item=item, is_admin=session.get('username') == 'admin')

@app.route('/delete_item/<int:id>', methods=['POST'])
def delete_item(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        execute_query('DELETE FROM stock_items WHERE id = %s', (id,))
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'error')
    
    return redirect(url_for('items'))

@app.route('/sales')
def sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get all sales
        sales_list = execute_query('SELECT * FROM sales ORDER BY sold_at DESC', fetch_all=True)
        
        # Get available items for sale
        available_items = execute_query('SELECT * FROM stock_items WHERE quantity > 0 ORDER BY name', fetch_all=True)
        
        return render_template('sales.html', sales=sales_list or [], available_items=available_items or [])
    except Exception as e:
        flash(f'Sales error: {str(e)}', 'error')
        return render_template('sales.html', sales=[], available_items=[])

@app.route('/sell_item/<int:id>', methods=['GET', 'POST'])
def sell_item(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get item details
    item = execute_query('SELECT * FROM stock_items WHERE id = %s', (id,), fetch_one=True)
    
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('sales'))
    
    if request.method == 'POST':
        try:
            quantity_sold = int(request.form['quantity_sold'])
            place = request.form.get('place', '')
            
            if quantity_sold > item['quantity']:
                flash('Not enough stock available', 'error')
                return redirect(url_for('sell_item', id=id))
            
            # Update item quantity
            new_quantity = item['quantity'] - quantity_sold
            execute_query('UPDATE stock_items SET quantity = %s, current_stock_value = %s WHERE id = %s', 
                          (new_quantity, new_quantity * item['selling_price'], id))
            
            # Add to sales
            total_amount = quantity_sold * item['selling_price']
            execute_query('''
                INSERT INTO sales (item_id, item_name, quantity_sold, selling_price, total_amount, 
                                 image_path, user_id, user_name, user_email, place)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (id, item['name'], quantity_sold, item['selling_price'], total_amount, 
                  item['image_path'], session['user_id'], session['username'], 
                  session['user_email'] if 'user_email' in session else '', place))
            
            flash(f'Sold {quantity_sold} {item["name"]} successfully!', 'success')
            return redirect(url_for('sales'))
        except Exception as e:
            flash(f'Error selling item: {str(e)}', 'error')
    
    return render_template('sell_item.html', item=item)

@app.route('/wages')
def wages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get total wages paid
        total_wages_result = execute_query('SELECT SUM(amount) as total FROM wages', fetch_one=True)
        total_wages = total_wages_result['total'] or 0
        
        # Get all wages
        wages_list = execute_query('SELECT * FROM wages ORDER BY created_at DESC', fetch_all=True)
        
        return render_template('wages.html', wages=wages_list or [], total_wages=total_wages)
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
            
            execute_query('INSERT INTO wages (employee_name, amount, wage_type, description) VALUES (%s, %s, %s, %s)', 
                          (employee_name, amount, wage_type, description))
            
            flash('Wage added successfully!', 'success')
            return redirect(url_for('wages'))
        except Exception as e:
            flash(f'Error adding wage: {str(e)}', 'error')
    
    return render_template('add_wage.html')

@app.route('/investment')
def investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['username'] != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get total investment
        total_invested_result = execute_query('SELECT SUM(CASE WHEN transaction_type = "invest" THEN amount ELSE -amount END) as total FROM investment_transactions', fetch_one=True)
        total_invested = total_invested_result['total'] or 0
        
        # Get stock value
        stock_value_result = execute_query('SELECT SUM(current_stock_value) as total FROM stock_items', fetch_one=True)
        stock_value = stock_value_result['total'] or 0
        
        # Get all transactions
        transactions = execute_query('SELECT * FROM investment_transactions ORDER BY created_at DESC', fetch_all=True)
        
        # Get items list
        items_list = execute_query('SELECT * FROM stock_items ORDER BY name', fetch_all=True)
        
        return render_template('investment.html', 
                             total_invested=total_invested,
                             stock_value=stock_value,
                             transactions=transactions or [],
                             items=items_list or [])
    except Exception as e:
        flash(f'Investment error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/investment/add', methods=['GET', 'POST'])
def add_investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['username'] != 'admin':
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
            
            execute_query('''
                INSERT INTO investment_transactions (transaction_type, amount, description, 
                                                 investor_name, investor_email, investor_phone)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (transaction_type, amount, description, investor_name, investor_email, investor_phone))
            
            flash(f'{transaction_type.title()} of ${amount:.2f} from {investor_name} recorded successfully!', 'success')
            return redirect(url_for('investment'))
        except Exception as e:
            flash(f'Error adding investment: {str(e)}', 'error')
    
    return render_template('add_investment.html')

@app.route('/investors')
def investors():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['username'] != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        transactions = execute_query('SELECT investor_name, investor_email, investor_phone, transaction_type, amount FROM investment_transactions', fetch_all=True)
        
        investor_data = {}
        for t in transactions or []:
            name, email, phone, type, amount = t['investor_name'], t['investor_email'], t['investor_phone'], t['transaction_type'], t['amount']
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
    
    if session['username'] != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        transactions = execute_query('SELECT * FROM investment_transactions WHERE investor_name = %s ORDER BY created_at DESC', (name,), fetch_all=True)
        
        # Calculate totals
        total_invested = sum(t['amount'] for t in (transactions or []) if t['transaction_type'] == 'invest')
        total_withdrawn = sum(t['amount'] for t in (transactions or []) if t['transaction_type'] == 'withdraw')
        balance = total_invested - total_withdrawn
        
        return render_template('investor_ledger.html', 
                             investor_name=name, 
                             transactions=transactions or [],
                             total_invested=total_invested,
                             total_withdrawn=total_withdrawn,
                             balance=balance)
    except Exception as e:
        flash(f'Investor ledger error: {str(e)}', 'error')
        return redirect(url_for('investors'))

if __name__ == '__main__':
    # Test database connection on startup
    if test_connection():
        print("Database connection test successful")
    else:
        print("Database connection test failed")
    
    # Ensure upload directory exists (only for local development)
    if not os.environ.get('RENDER'):  # Only create locally, not on Render
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
    
    port = int(os.environ.get('PORT', 5000))
    # Use production settings on Render
    debug = False if os.environ.get('RENDER') else True
    app.run(debug=debug, host='0.0.0.0', port=port)
