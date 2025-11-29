# Stock Monitoring System - Deployment Guide

## 🚀 Quick Deployment Options

### Option 1: Local Deployment (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```
Access: http://localhost:5000

---

### Option 2: Production Deployment with Gunicorn
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

### Option 3: Docker Deployment
Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t stock-monitor .
docker run -p 5000:5000 stock-monitor
```

---

### Option 4: Cloud Deployment (Heroku)
1. Install Heroku CLI
2. Create `Procfile`:
```
web: gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
3. Deploy:
```bash
heroku create your-app-name
git add .
git commit -m "Deploy stock monitoring system"
git push heroku main
```

---

## 📋 Pre-Deployment Checklist

### ✅ Security Updates
- [ ] Change Flask secret key in `app.py` line 11
- [ ] Update admin password from default "admin"
- [ ] Configure proper file permissions for uploads folder

### ✅ Database Setup
- [ ] Ensure `database.db` is included
- [ ] Test all database connections
- [ ] Verify user accounts work

### ✅ File Structure
- [ ] All templates in `templates/` folder
- [ ] `static/uploads/` folder exists and is writable
- [ ] `requirements.txt` is up to date

### ✅ Environment Variables (Optional)
Create `.env` file:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=/path/to/uploads
```

---

## 🔧 Production Configuration

### Update app.py for production:
```python
# Change line 11-12:
app.secret_key = 'your-secure-secret-key-here'
app.config['UPLOAD_FOLDER'] = '/path/to/secure/uploads'

# Update line 747:
app.run(debug=False, host='0.0.0.0', port=5000)
```

---

## 🌐 Access Information

### Default Login:
- **Username:** admin
- **Password:** admin

### Features:
- **User Registration** with profile photos
- **Admin Features:** Investment & Investor tracking
- **Sales Tracking** with location and user details
- **Item Management** with image uploads
- **Wages Management**

---

## 📱 Mobile Compatibility
- ✅ Responsive design
- ✅ Camera capture for sales
- ✅ Touch-friendly interface

---

## 🔍 Troubleshooting

### Common Issues:
1. **Port 5000 in use:** Change port in app.py line 747
2. **Upload folder permissions:** Ensure static/uploads is writable
3. **Database locked:** Restart application
4. **Images not showing:** Check static folder paths

### Support:
- Check Flask logs for errors
- Verify all dependencies are installed
- Test database connectivity

---

## 🎯 Success Metrics
- Application loads at http://your-domain:5000
- Users can register and login
- Admin can access investment features
- Sales tracking works with photos
- File uploads work correctly

Deploy and enjoy your Stock Monitoring System! 🚀
