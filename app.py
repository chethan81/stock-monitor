import os
from flask import Flask

app = Flask(__name__)
print("Flask app created successfully")
# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'stock-monitor-secret-2024-chethan81-production-key-1234567890')

@app.route('/')
def index():
    return '''
    <h1>Stock Monitor App is Running!</h1>
    <p><a href="/login">Go to Login</a></p>
    <p><a href="/test">Test Route</a></p>
    <p><a href="/dashboard">Dashboard</a></p>
    '''

@app.route('/test')
def test():
    return '''
    <h1>Test route working!</h1>
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
    port = int(os.environ.get('PORT', 10000))  # Render default is 10000
    app.run(host='0.0.0.0', port=port)
