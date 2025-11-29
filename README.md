# Stock Monitoring System

A complete, deployment-ready stock monitoring system built with Flask, SQLite, and HTML/CSS. Perfect for small businesses to track inventory, sales, and investments.

## Features

- 🔐 **Authentication**: Session-based login/logout with secure password hashing
- 📦 **Stock Management**: Full CRUD operations for inventory items
- 💰 **Sales Tracking**: Record sales and automatically update stock levels
- 📊 **Investment Analytics**: Track total investment and profit/loss
- 📱 **Mobile-Friendly**: Responsive design that works on all devices
- 🖼️ **Image Upload**: Support for product images with camera capture on mobile
- 🚀 **Cloud Ready**: Fully configured for Render.com deployment

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (auto-created)
- **Frontend**: HTML + CSS (clean, modern UI)
- **Deployment**: Render.com compatible
- **Authentication**: Werkzeug security

## Quick Start

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and go to `http://localhost:5000`

### Default Login Credentials
- **Username**: `admin`
- **Password**: `admin123`

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT (hashed)
);
```

### Stock Items Table
```sql
CREATE TABLE stock_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    quantity INTEGER,
    initial_price REAL,
    selling_price REAL,
    description TEXT,
    image_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Sales Table
```sql
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    item_name TEXT,
    quantity_sold INTEGER,
    selling_price REAL,
    total_amount REAL,
    sold_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT
);
```

## Project Structure

```
stock/
├── app.py                 # Main Flask application
├── database.db           # SQLite database (auto-created)
├── requirements.txt      # Python dependencies
├── render.yaml          # Render.com deployment config
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── login.html      # Login page
│   ├── dashboard.html  # Dashboard
│   ├── items.html      # Items list
│   ├── add_item.html   # Add item form
│   ├── edit_item.html  # Edit item form
│   ├── sell_item.html  # Sell item form
│   ├── sales.html      # Sales history
│   └── investment.html # Investment overview
├── static/
│   └── uploads/         # Uploaded images
└── README.md           # This file
```

## Deployment to Render.com

### Step 1: Push to GitHub

1. Create a new repository on GitHub
2. Push your code:

```bash
git init
git add .
git commit -m "Initial commit: Stock Monitoring System"
git branch -M main
git remote add origin https://github.com/yourusername/stock-monitoring-system.git
git push -u origin main
```

### Step 2: Deploy to Render

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will automatically detect the configuration from `render.yaml`
5. Click "Create Web Service"
6. Wait for deployment to complete (2-3 minutes)

### Step 3: Access Your App

Your app will be available at: `https://your-app-name.onrender.com`

## Features in Detail

### Dashboard
- Welcome message with user name
- Total items in stock
- Total investment amount
- Total revenue generated
- Total profit/loss calculation
- Recently added items with thumbnails
- Quick action buttons

### Stock Management
- Add new items with image upload
- Edit existing items
- Delete items (with image cleanup)
- Mark items as sold
- Automatic stock level updates
- Out of stock indicators

### Sales Module
- Record sales with quantity
- Automatic stock reduction
- Sales history with images
- Revenue calculations
- Sales analytics

### Investment Tracking
- Total investment overview
- Item-by-item cost breakdown
- Investment percentage visualization
- Average cost calculations
- Investment insights

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Protected routes
- SQL injection prevention
- File upload security
- CSRF protection ready

## Mobile Features

- Responsive design
- Camera capture support
- Touch-friendly interface
- Optimized for small screens

## Support

This application is production-ready and includes:
- Error handling
- Flash messages
- Form validation
- Image upload/delete
- Auto database creation
- Clean URL structure

## License

This project is open source and available under the MIT License.
