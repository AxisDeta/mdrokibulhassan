# MySQL Database Setup Guide

## Overview

Your Flask portfolio application now supports **both SQLite and MySQL** databases with automatic detection:

- **Development (Local):** Uses SQLite (`portfolio.db`) - No setup required
- **Production (Deployed):** Uses MySQL - Configure with environment variables

## How It Works

The app automatically detects which database to use:

```python
# If MySQL credentials are provided → Use MySQL
# If MySQL credentials are missing → Use SQLite
```

## Development Setup (SQLite)

**No changes needed!** Your current setup works as-is:

```bash
# Your .env file (or leave MySQL settings commented out)
FLASK_ENV=development
DATABASE_URL=sqlite:///portfolio.db
```

The app will use `portfolio.db` file in your project directory.

## Production Setup (MySQL)

### Step 1: Get MySQL Database

**Option A: PythonAnywhere (Recommended)**
1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Go to "Databases" tab
3. Create a MySQL database
4. Note down: hostname, username, password, database name

**Option B: Other Hosting Services**
- Railway: Provides MySQL addon
- PlanetScale: Free MySQL hosting
- AWS RDS: Professional MySQL hosting

### Step 2: Configure Environment Variables

Create or update your `.env` file on the production server:

```bash
# Production .env file
FLASK_ENV=production
SECRET_KEY=your-super-secret-random-key-here

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# MySQL Configuration
DB_HOST=your-mysql-host.mysql.pythonanywhere-services.com
DB_USER=your_username
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
DB_PORT=3306
```

### Step 3: Install Dependencies

On your production server:

```bash
pip install -r requirements.txt
```

This installs PyMySQL (MySQL driver) along with other dependencies.

### Step 4: Initialize Database

Run the initialization script to create tables:

```bash
python init_db.py
```

This creates all necessary tables in your MySQL database:
- `user` - Admin authentication
- `publication` - Research publications
- `message` - Contact form messages
- `research_area` - Research categories
- `profile_info` - Your profile data

### Step 5: Migrate Existing Data (Optional)

If you have existing data in SQLite that you want to move to MySQL:

**Option A: Use the scraper**
- Use the Google Scholar import feature to re-import publications

**Option B: Manual migration**
```bash
# Export from SQLite
python -c "from app import create_app; from models import *; app = create_app(); # export logic"

# Import to MySQL
# (Contact me if you need a migration script)
```

## Database Connection String Format

The app automatically builds the MySQL connection string:

```
mysql+pymysql://username:password@host:port/database?charset=utf8mb4
```

**Example:**
```
mysql+pymysql://myuser:mypass@db.example.com:3306/portfolio?charset=utf8mb4
```

## Verifying Your Setup

### Check Which Database is Being Used

Add this to your app startup to see which database is active:

```python
# In app.py, after app creation
print(f"Using database: {app.config['DATABASE_TYPE']}")
print(f"Connection: {app.config['SQLALCHEMY_DATABASE_URI']}")
```

### Test MySQL Connection

Create a test script:

```python
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        port=int(os.getenv('DB_PORT', 3306))
    )
    
    if connection.is_connected():
        print("✅ MySQL connection successful!")
        print(f"Database: {connection.database}")
        connection.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Troubleshooting

### "Access denied for user"
- Check username and password are correct
- Verify user has permissions on the database

### "Can't connect to MySQL server"
- Check DB_HOST is correct
- Verify DB_PORT (usually 3306)
- Check firewall settings
- Ensure database server is running

### "Unknown database"
- Verify DB_NAME exists
- Create database if needed: `CREATE DATABASE your_database_name;`

### "No module named 'pymysql'"
- Run: `pip install pymysql cryptography`

## PythonAnywhere Specific Setup

### 1. Upload Your Code
```bash
# On PythonAnywhere console
git clone https://github.com/yourusername/Research-Paper-Tool.git
cd Research-Paper-Tool
```

### 2. Create Virtual Environment
```bash
mkvirtualenv --python=/usr/bin/python3.10 portfolio-env
pip install -r requirements.txt
```

### 3. Configure Database
- Go to "Databases" tab
- Initialize MySQL database
- Note the connection details

### 4. Set Environment Variables
Create `.env` file:
```bash
nano .env
# Paste your production config
```

### 5. Configure WSGI
Edit `/var/www/yourusername_pythonanywhere_com_wsgi.py`:

```python
import sys
import os

# Add your project directory
project_home = '/home/yourusername/Research-Paper-Tool'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from app import create_app
application = create_app()
```

### 6. Initialize Database
```bash
cd ~/Research-Paper-Tool
python init_db.py
```

### 7. Reload Web App
- Go to "Web" tab
- Click "Reload" button

## Security Best Practices

1. **Never commit `.env` to Git**
   ```bash
   # Add to .gitignore
   .env
   *.db
   ```

2. **Use strong passwords**
   - Generate random SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Use complex admin password

3. **Restrict database access**
   - Only allow connections from your app server
   - Use strong MySQL password

4. **Regular backups**
   - PythonAnywhere: Automatic backups available
   - Manual: `mysqldump -u user -p database > backup.sql`

## Summary

✅ **Development:** SQLite (automatic, no setup)
✅ **Production:** MySQL (configure environment variables)
✅ **Automatic Detection:** App chooses database based on config
✅ **No Code Changes:** Same codebase works for both environments

Your app is now ready for production deployment with MySQL!
