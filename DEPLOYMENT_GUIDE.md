# 🚀 Stock Monitor - Free Hosting Deployment Guide
## Deploy SQLite → MySQL for 1+ Year Free Hosting

### 📋 Overview
- **Backend**: Render Free Tier (Flask)
- **Database**: Railway MySQL Free Tier
- **Images**: Cloudinary Free Tier (Optional)
- **Duration**: Reliable for 1+ years on free tiers

---

## 🔧 Step A: Create Railway MySQL Database

1. **Sign up for Railway**
   - Go to [railway.app](https://railway.app)
   - Create free account with GitHub

2. **Create MySQL Database**
   - Click "New Project" → "Provision MySQL"
   - Select "MySQL" (not PostgreSQL)
   - Choose free tier ($0/month)
   - Wait for deployment (2-3 minutes)

3. **Get Database Credentials**
   - Click on your MySQL database
   - Go to "Connect" tab
   - Copy these values:
     ```
     DB_HOST: containers-us-west-1.railway.app (or similar)
     DB_PORT: 6789 (or shown port)
     DB_USER: root
     DB_PASSWORD: [copy password]
     DB_NAME: railway (or shown database)
     ```

---

## 🔧 Step B: Configure Render Environment Variables

1. **Sign up for Render**
   - Go to [render.com](https://render.com)
   - Create free account with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     ```
     Name: stock-monitor
     Environment: Python 3
     Region: Oregon (free tier)
     Branch: main
     Build Command: pip install -r requirements.txt
     Start Command: gunicorn app:app
     ```

3. **Add Environment Variables**
   - Go to "Environment" tab
   - Add these variables:
     ```
     SECRET_KEY=your-unique-secret-key-here
     DB_HOST=containers-us-west-1.railway.app
     DB_PORT=6789
     DB_USER=root
     DB_PASSWORD=your-railway-mysql-password
     DB_NAME=railway
     ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)

---

## 🔧 Step C: Run MySQL Schema Once

**Option 1: Using Railway MySQL Console (Recommended)**
1. Go to your Railway MySQL database
2. Click "MySQL Console" tab
3. Copy-paste the entire contents of `mysql_schema.sql`
4. Click "Execute" or press Enter
5. Verify tables created: `SHOW TABLES;`

**Option 2: Using MySQL Workbench (Local)**
1. Install MySQL Workbench
2. Connect using Railway credentials
3. Open `mysql_schema.sql` file
4. Execute all queries

**Option 3: Using Command Line**
```bash
mysql -h containers-us-west-1.railway.app -P 6789 -u root -p railway < mysql_schema.sql
```

---

## 🔧 Step D: Deploy Flask Backend on Render

1. **Verify Files Exist**
   Ensure these files are in your repository:
   ```
   app.py
   database.py
   requirements.txt
   Procfile
   .env.example
   mysql_schema.sql
   ```

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Upgrade to MySQL for free hosting"
   git push origin main
   ```

3. **Monitor Deployment**
   - Render will auto-deploy on push
   - Check "Logs" tab for any errors
   - Wait for "Live" status

---

## 🔧 Step E: Test Routes & Verify No Data Loss

1. **Basic Tests**
   - Open your Render URL: `https://stock-monitor.onrender.com`
   - Test login: `admin` / `admin123`
   - Add a test item
   - Create a test sale
   - Check dashboard statistics

2. **Data Persistence Tests**
   - Add data, wait 5 minutes, refresh → data should persist
   - Logout/login → data should persist
   - Check if calculations work correctly

3. **Long-term Tests**
   - Visit again after 30 minutes → should work after Render "sleep"
   - Test after Railway database restart → should auto-reconnect

---

## 🛠️ Optional: Cloudinary for Images

If you have image uploads:

1. **Setup Cloudinary Free**
   - Sign up at [cloudinary.com](https://cloudinary.com)
   - Get free API credentials

2. **Add Environment Variables**
   ```
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```

3. **Install Cloudinary**
   ```bash
   pip install cloudinary
   ```
   Add to requirements.txt: `cloudinary==1.36.0`

---

## 🔍 Troubleshooting

### Common Issues & Solutions:

**1. Database Connection Failed**
```
Error: Access denied for user 'root'@'%'
```
- Verify DB_PASSWORD matches Railway exactly
- Check DB_HOST and DB_PORT are correct
- Ensure Railway MySQL is running

**2. ModuleNotFoundError: No module named 'mysql.connector'**
- Wait 5-10 minutes for Render to install dependencies
- Check requirements.txt has correct package name
- Redeploy if needed

**3. 500 Internal Server Error**
- Check Render "Logs" tab
- Verify all environment variables are set
- Ensure mysql_schema.sql was executed

**4. Data Not Saving**
- Verify database schema was created
- Check if user has proper permissions
- Test database connection manually

**5. App Sleeps After Inactivity**
- This is normal on free tiers
- App should wake up on next request
- Data persists in MySQL database

---

## 📊 Free Tier Limits (Current 2024):

**Render Free Tier:**
- 750 hours/month (enough for 24/7)
- 512MB RAM
- Shared CPU
- Automatic sleep after 15 min inactivity

**Railway MySQL Free Tier:**
- 500MB storage
- 100 hours/month runtime
- Auto-pauses after inactivity
- Instant wake on connection

**Cloudinary Free Tier:**
- 25GB storage
- 25GB bandwidth/month
- All image transformations

---

## 🔄 Maintenance Tips:

1. **Monthly Check**
   - Verify Railway database hasn't exceeded limits
   - Check Render usage statistics
   - Monitor error logs

2. **Backup Data**
   - Export MySQL data monthly
   - Keep local copy of important data

3. **Performance**
   - Database queries are optimized with indexes
   - Connection pooling prevents overload
   - Auto-reconnection handles wake-ups

---

## 🎉 Success Criteria:

✅ Database persists across deployments  
✅ Data survives Render sleep/wake cycles  
✅ No files stored on Render filesystem  
✅ Auto-reconnection to MySQL database  
✅ Works reliably for 1+ years on free tiers  

Your Stock Monitor is now ready for production! 🚀
