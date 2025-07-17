# Deployment Guide for SkillSwap

This guide explains how to deploy the SkillSwap Flask application to various hosting platforms.

## Quick Start with GitHub

1. **Initialize Git Repository**
```bash
cd dam
git init
git add .
git commit -m "Initial commit: SkillSwap Flask application"
```

2. **Connect to GitHub**
```bash
git remote add origin https://github.com/aminahnabeel/SkillSwap.git
git branch -M main
git push -u origin main
```

3. **Enable GitHub Pages**
   - Go to your repository settings
   - Navigate to "Pages" section
   - Select "Deploy from a branch"
   - Choose "main" branch and "/docs" folder
   - Your documentation will be available at: `https://aminahnabeel.github.io/SkillSwap/`

## Deployment Options

### Option 1: Heroku (Recommended)

1. **Install Heroku CLI**
   - Download from https://devcenter.heroku.com/articles/heroku-cli

2. **Deploy to Heroku**
```bash
heroku login
heroku create skillswap-app
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

3. **Configure Database**
   - Update database connection to use PostgreSQL instead of SQL Server
   - Install psycopg2: `pip install psycopg2`

### Option 2: Railway

1. **Connect GitHub Repository**
   - Go to https://railway.app
   - Sign up and connect your GitHub account
   - Deploy from your SkillSwap repository

2. **Add Database**
   - Add PostgreSQL plugin in Railway dashboard
   - Update connection string in your app

### Option 3: Render

1. **Connect Repository**
   - Go to https://render.com
   - Create new Web Service from GitHub repository

2. **Configure Build**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

### Option 4: PythonAnywhere

1. **Upload Files**
   - Upload your project files to PythonAnywhere

2. **Configure Web App**
   - Create new web app
   - Set WSGI file to point to your Flask app

## Database Configuration

### For Production (PostgreSQL)

Update your `app.py` to support both SQL Server (development) and PostgreSQL (production):

```python
import os
import psycopg2
from urllib.parse import urlparse

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production - PostgreSQL
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    else:
        # Development - SQL Server
        try:
            conn = pyodbc.connect(
               'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=localhost\\SQLEXPRESS02;'
                'DATABASE=skillswaps;'
                'Trusted_Connection=yes;'
            )
            return conn
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return None
```

## Environment Variables

Create a `.env` file for local development:

```
DATABASE_URL=your_local_database_url
SECRET_KEY=your_secret_key
FLASK_ENV=development
```

For production, set these in your hosting platform's environment variables.

## Database Migration

You'll need to create database tables on your production database. Consider using:

1. **Flask-Migrate** for database migrations
2. **SQL scripts** to create tables
3. **Database initialization** endpoint

## Security Considerations

1. **Environment Variables**: Store sensitive data in environment variables
2. **HTTPS**: Enable HTTPS in production
3. **Database Security**: Use connection pooling and prepared statements
4. **Session Security**: Use secure session configurations

## Monitoring and Maintenance

1. **Logging**: Implement proper logging for production
2. **Error Tracking**: Use services like Sentry
3. **Database Backups**: Regular backup strategy
4. **Performance Monitoring**: Monitor application performance

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check connection string format
   - Verify database credentials
   - Ensure database server is accessible

2. **Static Files Not Loading**
   - Configure static file serving
   - Check file paths in templates

3. **WebSocket Issues**
   - Verify WebSocket support on hosting platform
   - Check firewall settings

### Getting Help

- Check the GitHub repository issues
- Review deployment platform documentation
- Test locally before deploying

## Cost Estimates

- **Heroku**: Free tier available, paid plans start at $7/month
- **Railway**: Free tier with limits, paid plans start at $5/month
- **Render**: Free tier available, paid plans start at $7/month
- **PythonAnywhere**: Free tier available, paid plans start at $5/month

Choose the platform that best fits your needs and budget.
