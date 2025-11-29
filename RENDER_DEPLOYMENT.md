# 🚀 Render Deployment Guide - Stock Monitoring System

## 📋 Prerequisites
- GitHub account
- Render account (free tier available)
- All project files ready

---

## 🗂️ Project Structure (Ready for Render)
```
stock/
├── app.py                    # ✅ Updated for Render
├── requirements.txt          # ✅ Includes gunicorn
├── Procfile                  # ✅ Render process file
├── runtime.txt               # ✅ Python 3.9.16
├── .gitignore               # ✅ Proper ignore rules
├── database.db              # ✅ SQLite database
├── static/
│   └── uploads/
│       └── .gitkeep         # ✅ Keeps uploads folder
└── templates/               # ✅ All HTML templates
```

---

## 🚀 Step-by-Step Render Deployment

### Step 1: Push to GitHub
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Ready for Render deployment"

# Create GitHub repository
# Go to github.com → New repository → Copy the URL

# Push to GitHub
git remote add origin https://github.com/yourusername/stock-monitor.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render
1. **Sign up/Login** to [render.com](https://render.com)
2. **Click "New +"** → "Web Service"
3. **Connect GitHub** → Authorize and select your repository
4. **Configure Service:**
   - **Name:** `stock-monitor` (or your choice)
   - **Region:** Choose nearest
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:5000 app:app`

### Step 3: Add Environment Variables
In Render Dashboard → Your Service → Environment:
```
SECRET_KEY=your-secure-secret-key-here
UPLOAD_FOLDER=/app/static/uploads
DATABASE_PATH=/app/database.db
PORT=5000
```

### Step 4: Deploy!
Click **"Create Web Service"** and wait for deployment.

---

## 🔧 Render-Specific Configurations

### ✅ What's Already Configured:
- **Procfile** tells Render how to run your app
- **runtime.txt** specifies Python version
- **app.py** uses environment variables
- **requirements.txt** includes all dependencies
- **Port 5000** (Render's default)

### 🌐 After Deployment:
Your app will be available at: `https://your-service-name.onrender.com`

---

## 📱 Free Tier Limitations
- **750 hours/month** runtime
- **Sleeps after 15 minutes** inactivity
- **Takes ~30 seconds** to wake up
- **512MB RAM** limit
- **No custom domain** on free tier

---

## 🔍 Troubleshooting

### Common Issues:
1. **Build Failed:** Check requirements.txt and Python version
2. **Database Error:** Ensure SQLite works on Render
3. **Upload Issues:** Check folder permissions
4. **App Not Loading:** Wait for full deployment

### Debug on Render:
- Go to Render Dashboard → Your Service → Logs
- Check build and runtime logs
- Environment variables in Settings tab

---

## 🚀 Alternative: Render PostgreSQL (Recommended)

For better performance, switch to PostgreSQL:

### Update app.py:
```python
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db():
    if os.environ.get('DATABASE_URL'):
        # Use PostgreSQL on Render
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    else:
        # Use SQLite locally
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
```

### Add to requirements.txt:
```
psycopg2-binary==2.9.7
```

### On Render:
- Add PostgreSQL database
- Use `DATABASE_URL` environment variable

---

## 🎯 Success Checklist
- [ ] GitHub repository created
- [ ] All files pushed to GitHub
- [ ] Render service created
- [ ] Environment variables set
- [ ] App loads at Render URL
- [ ] User registration works
- [ ] Admin features accessible
- [ ] File uploads work

---

## 💡 Pro Tips
1. **Use PostgreSQL** for better performance
2. **Monitor logs** regularly
3. **Set up backups** for database
4. **Upgrade plan** for more features
5. **Custom domain** with paid plan

---

## 🆘 Support
- **Render Docs:** https://render.com/docs
- **Flask on Render:** https://render.com/docs/deploy-flask
- **Community:** https://community.render.com

Your Stock Monitoring System is ready for Render! 🚀
