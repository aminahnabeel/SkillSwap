# SkillSwap - Peer-to-Peer Skill Exchange Platform

A Flask-based web application that enables users to exchange skills with each other in a peer-to-peer marketplace.

## Features

- **User Authentication**: Secure login and registration system
- **Skill Management**: Add, edit, and showcase your skills
- **Skill Requests**: Create requests for skills you want to learn
- **Matching System**: Automatic matching between skill providers and requesters
- **Real-time Messaging**: Chat with other users using WebSocket connections
- **Transaction Management**: Schedule and track skill exchange sessions
- **Review System**: Rate and review completed exchanges
- **Notifications**: Stay updated on matches, messages, and activities

## Technologies Used

- **Backend**: Flask, Flask-SocketIO
- **Database**: SQL Server with pyodbc
- **Frontend**: HTML, CSS, JavaScript
- **Real-time Communication**: WebSockets
- **Authentication**: Session-based with secure password hashing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aminahnabeel/SkillSwap.git
cd SkillSwap
```

2. Install required dependencies:
```bash
pip install flask flask-socketio pyodbc
```

3. Set up SQL Server database:
   - Create a database named `skillswaps`
   - Update the connection string in `app.py` with your SQL Server details
   - Run the database schema scripts (if available)

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
SkillSwap/
├── app.py                 # Main Flask application
├── static/               # Static files (CSS, JS, images)
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── img/             # Images
├── templates/           # HTML templates
│   ├── partials/        # Partial templates
│   └── *.html          # Page templates
└── README.md           # This file
```

## Database Schema

The application uses SQL Server with the following main tables:
- `Users` - User account information
- `Skills` - Available skills in the system
- `UserSkills` - Skills that users possess
- `SkillRequests` - Requests for specific skills
- `Matches` - Matches between skill providers and requesters
- `Transactions` - Scheduled skill exchange sessions
- `Messages` - User-to-user messaging
- `Reviews` - User reviews and ratings
- `Notifications` - System notifications

## Key Features

### User Management
- Secure registration and login
- Profile management with bio and location
- Skill portfolio management

### Skill Exchange
- Browse available skills by category
- Create skill requests with urgency levels
- Automatic matching system
- Schedule and manage transactions

### Communication
- Real-time messaging system
- Notification system for important updates
- Review and rating system

## Configuration

Update the database connection settings in `app.py`:

```python
def get_db_connection():
    try:
        conn = pyodbc.connect(
           'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=your_server_name;'
            'DATABASE=skillswaps;'
            'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None
```

## Deployment

This Flask application can be deployed to various platforms:

- **Heroku**: Platform-as-a-Service with database add-ons
- **Railway**: Modern deployment platform
- **PythonAnywhere**: Python-focused hosting
- **Render**: Full-stack application hosting

For production deployment, consider:
- Using environment variables for sensitive configuration
- Implementing proper logging
- Adding database migration scripts
- Setting up SSL certificates
- Configuring production WSGI server (e.g., Gunicorn)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions, please open an issue on the GitHub repository.
