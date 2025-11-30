import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import execute_query, init_database, test_connection

app = Flask(__name__)
print("Flask app created successfully")
# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')

# Initialize database on startup (with better error handling)
# Railway MySQL integration - v2 - port fix
try:
    print("Starting database initialization...")
    init_database()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization failed: {e}")
    print("App will continue without database - basic routes will work")

@app.route('/')
def index():
    try:
        # Try to get dashboard stats if database works
        if test_connection():
            return '''
            <h1>🎉 Stock Monitor - Database Connected!</h1>
            <p><a href="/login">Login to Dashboard</a></p>
            <p><a href="/test">Database Test</a></p>
            <p><strong>Status:</strong> ✅ Database Connected</p>
            '''
        else:
            return '''
            <h1>Stock Monitor App is Running!</h1>
            <p><a href="/login">Go to Login</a></p>
            <p><a href="/test">Test Route</a></p>
            <p><a href="/dashboard">Dashboard</a></p>
            <p><strong>Status:</strong> ⚠️ Database Connection Issue</p>
            '''
    except Exception as e:
        return f'''
        <h1>Stock Monitor App is Running!</h1>
        <p><a href="/login">Go to Login</a></p>
        <p><a href="/test">Test Route</a></p>
        <p><a href="/dashboard">Dashboard</a></p>
        <p><strong>Status:</strong> ❌ Database Error: {str(e)}</p>
        '''

@app.route('/test')
def test():
    try:
        if test_connection():
            return '''
            <h1>✅ Database Connection Successful!</h1>
            <p>Railway MySQL is working perfectly!</p>
            <p><a href="/login">Go to Login</a></p>
            <p><a href="/">Back to Home</a></p>
            '''
        else:
            return '''
            <h1>❌ Database Connection Failed</h1>
            <p>Having trouble connecting to Railway MySQL</p>
            <p><a href="/login">Go to Login</a></p>
            <p><a href="/">Back to Home</a></p>
            '''
    except Exception as e:
        return f'''
        <h1>❌ Database Error</h1>
        <p>Error: {str(e)}</p>
        <p><a href="/login">Go to Login</a></p>
        <p><a href="/">Back to Home</a></p>
        '''

@app.route('/login')
def login():
    return '''
    <h1>Login page - basic version working!</h1>
    <br><br>
    <a href="/" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Back to Home</a>
    <br><br>
    <a href="/dashboard" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Dashboard</a>
    '''

@app.route('/dashboard')
def dashboard():
    return '''
    <h1>Dashboard - basic version working!</h1>
    <p><a href="/login">Back to Login</a></p>
    <p><a href="/">Back to Home</a></p>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render expects port 10000
    app.run(host='0.0.0.0', port=port)
