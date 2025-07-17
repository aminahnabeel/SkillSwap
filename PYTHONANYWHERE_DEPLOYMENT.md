# PythonAnywhere Deployment Guide for SkillSwap

This guide will help you deploy your SkillSwap Flask application to PythonAnywhere.

## Prerequisites

1. **PythonAnywhere Account**: Sign up at https://www.pythonanywhere.com/
2. **GitHub Repository**: Your code should be in your GitHub repository at https://github.com/aminahnabeel/SkillSwap

## Step 1: Set Up Your PythonAnywhere Environment

### 1.1 Create a Web App
1. Go to your PythonAnywhere dashboard
2. Click on "Web" tab
3. Click "Add a new web app"
4. Choose "Flask" as the framework
5. Choose Python 3.10 (or latest available)
6. Set the path to `/home/yourusername/SkillSwap/flask_app.py` (replace `yourusername` with your actual username)

### 1.2 Clone Your Repository
Open a Bash console in PythonAnywhere and run:
```bash
cd ~
git clone https://github.com/aminahnabeel/SkillSwap.git
cd SkillSwap
```

### 1.3 Install Dependencies
In your Bash console:
```bash
pip3.10 install --user -r requirements.txt
```

## Step 2: Set Up MySQL Database

### 2.1 Create MySQL Database
1. Go to "Databases" tab in PythonAnywhere dashboard
2. Create a new MySQL database named `yourusername$skillswaps`
3. Note down your database connection details

### 2.2 Create Database Tables
You'll need to create the database schema. In your Bash console:
```bash
mysql -u yourusername -p'your-password' -h yourusername.mysql.pythonanywhere-services.com yourusername$skillswaps
```

Then run your SQL schema creation commands. Here's a basic example:
```sql
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Bio TEXT,
    Location VARCHAR(100),
    ReputationScore INT DEFAULT 0,
    IsActive BOOLEAN DEFAULT TRUE,
    JoinDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastActive DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Categories (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL UNIQUE,
    Description TEXT,
    IsActive BOOLEAN DEFAULT TRUE
);

CREATE TABLE Skills (
    SkillID INT AUTO_INCREMENT PRIMARY KEY,
    SkillName VARCHAR(100) NOT NULL,
    Description TEXT,
    CategoryID INT,
    IsActive BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
);

-- Add more tables as needed for your application
```

## Step 3: Configure Your Application

### 3.1 Update flask_app.py
Edit the `flask_app.py` file with your actual details:

```python
#!/usr/bin/python3.10

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/SkillSwap'  # Replace 'yourusername' with your actual username
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables for PythonAnywhere
os.environ['PYTHONANYWHERE_SITE'] = 'true'

# Database configuration
os.environ['MYSQL_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['MYSQL_USER'] = 'yourusername'
os.environ['MYSQL_PASSWORD'] = 'your-mysql-password'
os.environ['MYSQL_DATABASE'] = 'yourusername$skillswaps'

# Secret key for sessions
os.environ['SECRET_KEY'] = 'your-very-secure-secret-key-here'

from app import app as application

if __name__ == "__main__":
    application.run()
```

### 3.2 Update Web App Configuration
1. Go to "Web" tab in PythonAnywhere
2. In the "Code" section, set:
   - **Source code**: `/home/yourusername/SkillSwap/`
   - **Working directory**: `/home/yourusername/SkillSwap/`
   - **WSGI configuration file**: `/home/yourusername/SkillSwap/flask_app.py`

### 3.3 Set Static Files
In the "Static files" section, add:
- **URL**: `/static/`
- **Directory**: `/home/yourusername/SkillSwap/static/`

## Step 4: Test Your Application

### 4.1 Reload Your Web App
1. Go to "Web" tab
2. Click "Reload yourusername.pythonanywhere.com"

### 4.2 Check Error Logs
If there are issues, check the error logs:
1. Go to "Web" tab
2. Click on "Error log" to see what's wrong

### 4.3 Access Your Application
Visit: `https://yourusername.pythonanywhere.com`

## Step 5: Database Migration (SQL Server to MySQL)

Since your original application uses SQL Server, you'll need to adapt the SQL queries for MySQL. Here are the main differences:

### 5.1 Date Functions
- SQL Server: `GETDATE()` → MySQL: `NOW()`
- SQL Server: `DATEADD()` → MySQL: `DATE_ADD()`

### 5.2 Identity Columns
- SQL Server: `SELECT @@IDENTITY` → MySQL: `SELECT LAST_INSERT_ID()`

### 5.3 TOP Clause
- SQL Server: `SELECT TOP 10` → MySQL: `SELECT ... LIMIT 10`

### 5.4 Update Your Queries
You'll need to update your SQL queries in `app.py`. For example:

```python
# Change this:
cursor.execute("SELECT @@IDENTITY AS ID")

# To this:
cursor.execute("SELECT LAST_INSERT_ID() AS ID")
```

## Step 6: Important Notes

### 6.1 WebSocket Limitations
PythonAnywhere's free and paid plans have limitations with WebSocket connections. The real-time messaging features might not work as expected. Consider:
- Using AJAX polling instead of WebSockets
- Upgrading to a plan that supports WebSockets
- Using alternative real-time solutions

### 6.2 File Structure
Ensure your file structure matches:
```
/home/yourusername/SkillSwap/
├── app.py
├── flask_app.py
├── requirements.txt
├── static/
│   ├── css/
│   ├── js/
│   └── img/
└── templates/
    └── *.html
```

### 6.3 Security Considerations
- Use environment variables for sensitive data
- Generate a secure secret key
- Use HTTPS (automatically provided by PythonAnywhere)
- Regularly update dependencies

## Step 7: Updates and Maintenance

### 7.1 Updating Your Code
To update your application:
```bash
cd ~/SkillSwap
git pull origin main
pip3.10 install --user -r requirements.txt
```

Then reload your web app from the PythonAnywhere dashboard.

### 7.2 Database Backups
Regularly backup your database:
```bash
mysqldump -u yourusername -p'your-password' -h yourusername.mysql.pythonanywhere-services.com yourusername$skillswaps > backup.sql
```

## Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure all dependencies are installed with `pip3.10 install --user`
2. **Database Connection**: Verify your MySQL credentials and database name
3. **Static Files**: Ensure static files are properly configured in the Web tab
4. **Permission Issues**: Check file permissions if you encounter access errors

### Getting Help:
- Check PythonAnywhere forums: https://www.pythonanywhere.com/forums/
- PythonAnywhere help pages: https://help.pythonanywhere.com/
- Check error logs in the Web tab of your dashboard

## Cost Information
- **Free Tier**: Limited CPU seconds, one web app
- **Paid Plans**: Start from $5/month, more resources and features
- **Database**: MySQL included in all plans

Your SkillSwap application should now be accessible at `https://yourusername.pythonanywhere.com`!
