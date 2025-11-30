import os
from flask import Flask

app = Flask(__name__)
print("Flask app created successfully")
# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')

@app.route('/')
def index():
    return "Stock Monitor App is Running! <a href='/login'>Go to Login</a>"

@app.route('/test')
def test():
    return "Test route working! <a href='/login'>Go to Login</a>"

@app.route('/login')
def login():
    return "Login page - basic version working! <a href='/'>Back to Home</a>"

@app.route('/dashboard')
def dashboard():
    return "Dashboard - basic version working! <a href='/login'>Back to Login</a>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
