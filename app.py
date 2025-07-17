from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import pyodbc
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app)

# Database connection
def get_db_connection():
    try:
        conn = pyodbc.connect(
           'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost\SQLEXPRESS02;'  # Replace with your server
            'DATABASE=skillswaps;'  # Replace with your database name
            'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

# Add a function to check database connection
def test_db_connection():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        return False
    except Exception as e:
        print(f"Database test connection error: {str(e)}")
        return False

# User authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    # Check database connection on homepage load
    db_connected = test_db_connection()
    if not db_connected:
        flash('Database connection error. Please contact support.', 'error')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('login.html')
            
        cursor = conn.cursor()
        
        # Get user from database
        cursor.execute("SELECT UserID, Username, PasswordHash FROM Users WHERE Username = ?", (username,))
        user = cursor.fetchone()
        
        if user and verify_password(password, user.PasswordHash):
            session['user_id'] = user.UserID
            session['username'] = user.Username
            
            # Update last active
            cursor.execute("UPDATE Users SET LastActive = GETDATE() WHERE UserID = ?", (user.UserID,))
            conn.commit()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
        
        conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        # Hash password
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('register.html')
            
        cursor = conn.cursor()
        
        try:
            # Check if username or email already exists
            cursor.execute("SELECT UserID FROM Users WHERE Username = ? OR Email = ?", (username, email))
            if cursor.fetchone():
                flash('Username or email already exists', 'error')
                return render_template('register.html')
            
            # Insert new user
            cursor.execute("""
                INSERT INTO Users (Username, Email, PasswordHash, FirstName, LastName, JoinDate, LastActive)
                VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (username, email, password_hash, first_name, last_name))
            conn.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# FIXED: Dashboard route with corrected logic and column names
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    # Get user profile
    cursor.execute("SELECT * FROM Users WHERE UserID = ?", (user_id,))
    user = cursor.fetchone()
    
    # Get user skills
    cursor.execute("""
        SELECT us.*, s.SkillName, c.CategoryName
        FROM UserSkills us
        JOIN Skills s ON us.SkillID = s.SkillID
        JOIN Categories c ON s.CategoryID = c.CategoryID
        WHERE us.UserID = ?
    """, (user_id,))
    skills = cursor.fetchall()
    
    # Get pending requests created by current user
    cursor.execute("""
        SELECT sr.*, s.SkillName
        FROM SkillRequests sr
        JOIN Skills s ON sr.SkillID = s.SkillID
        WHERE sr.UserID = ? AND sr.Status = 'Open'
    """, (user_id,))
    requests = cursor.fetchall()
    
    # FIXED: Get matches where current user is the REQUESTOR (can accept offers)
    cursor.execute("""
        SELECT m.MatchID, m.Status, m.RequestID, m.ProviderUserID, m.RequestorUserID,
               u.Username as ProviderUsername, s.SkillName
        FROM Matches m
        JOIN Users u ON m.ProviderUserID = u.UserID
        JOIN SkillRequests sr ON m.RequestID = sr.RequestID
        JOIN Skills s ON sr.SkillID = s.SkillID
        WHERE m.RequestorUserID = ? AND m.Status = 'Pending'
    """, (user_id,))
    matches_as_requestor = cursor.fetchall()
    
    # FIXED: Get matches where current user is the PROVIDER (waiting for acceptance)
    cursor.execute("""
        SELECT m.MatchID, m.Status, m.RequestID, m.ProviderUserID, m.RequestorUserID,
               u.Username as RequestorUsername, s.SkillName
        FROM Matches m
        JOIN Users u ON m.RequestorUserID = u.UserID
        JOIN SkillRequests sr ON m.RequestID = sr.RequestID
        JOIN Skills s ON sr.SkillID = s.SkillID
        WHERE m.ProviderUserID = ? AND m.Status = 'Pending'
    """, (user_id,))
    matches_as_provider = cursor.fetchall()
    
    # Get accepted matches for both roles
    cursor.execute("""
        SELECT m.MatchID, m.Status, m.RequestID, m.ProviderUserID, m.RequestorUserID,
               CASE WHEN m.RequestorUserID = ? THEN u2.Username ELSE u1.Username END as OtherUsername,
               CASE WHEN m.RequestorUserID = ? THEN u2.UserID ELSE u1.UserID END as OtherUserID,
               s.SkillName,
               CASE WHEN m.RequestorUserID = ? THEN 'Requestor' ELSE 'Provider' END as MyRole
        FROM Matches m
        JOIN Users u1 ON m.RequestorUserID = u1.UserID
        JOIN Users u2 ON m.ProviderUserID = u2.UserID
        JOIN SkillRequests sr ON m.RequestID = sr.RequestID
        JOIN Skills s ON sr.SkillID = s.SkillID
        WHERE (m.RequestorUserID = ? OR m.ProviderUserID = ?) AND m.Status = 'Accepted'
    """, (user_id, user_id, user_id, user_id, user_id))
    accepted_matches = cursor.fetchall()
    
    # Get unread notifications (using a more generic approach)
    try:
        cursor.execute("""
            SELECT *
            FROM Notifications
            WHERE UserID = ? AND IsRead = 0
            ORDER BY CreatedDate DESC
        """, (user_id,))
        notifications = cursor.fetchall()
    except:
        # If CreatedDate doesn't exist, try without ORDER BY
        cursor.execute("""
            SELECT *
            FROM Notifications
            WHERE UserID = ? AND IsRead = 0
        """, (user_id,))
        notifications = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                          user=user, 
                          skills=skills, 
                          requests=requests, 
                          matches_as_requestor=matches_as_requestor,
                          matches_as_provider=matches_as_provider,
                          accepted_matches=accepted_matches,
                          notifications=notifications)

@app.route('/profile')
@login_required
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    profile_id = request.args.get('user_id', user_id)
    
    # Check if viewing own profile or someone else's
    is_own_profile = str(profile_id) == str(user_id)
    
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('index'))
            
        cursor = conn.cursor()
        
        # Fetch user information
        user_query = """
            SELECT UserID, Username, Email, FirstName, LastName, Bio, Location, JoinDate
            FROM Users 
            WHERE UserID = ?
        """
        cursor.execute(user_query, (profile_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            flash('User not found.', 'error')
            return redirect(url_for('login'))
        
        # Convert user row to dictionary for easier template access
        user_dict = {
            'UserID': user_row[0],
            'Username': user_row[1],
            'Email': user_row[2],
            'FirstName': user_row[3],
            'LastName': user_row[4],
            'Bio': user_row[5],
            'Location': user_row[6],
            'CreatedAt': user_row[7],
            'is_own_profile': is_own_profile  # Add this flag
        }
        
        # Fetch user skills with skill details
        skills_query = """
            SELECT 
                us.UserSkillID,
                us.SkillID,
                s.SkillName,
                COALESCE(c.CategoryName, 'General') as Category,
                us.ProficiencyLevel,
                us.YearsExperience,
                us.IsVerified,
                us.VerificationDate,
                us.CreatedDate
            FROM UserSkills us
            INNER JOIN Skills s ON us.SkillID = s.SkillID
            LEFT JOIN Categories c ON s.CategoryID = c.CategoryID
            WHERE us.UserID = ?
            ORDER BY us.CreatedDate DESC
        """
        cursor.execute(skills_query, (profile_id,))
        skills_rows = cursor.fetchall()
        
        # Convert skills to list of dictionaries
        user_skills = []
        for skill in skills_rows:
            skill_dict = {
                'UserSkillID': skill[0],
                'SkillID': skill[1],
                'SkillName': skill[2],
                'Category': skill[3],
                'ProficiencyLevel': skill[4],
                'YearsExperience': skill[5],
                'IsVerified': bool(skill[6]) if skill[6] is not None else False,
                'VerificationDate': skill[7],
                'CreatedDate': skill[8]
            }
            user_skills.append(skill_dict)
        
        # Get skill statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_skills,
                COUNT(CASE WHEN IsVerified = 1 THEN 1 END) as verified_skills,
                COUNT(CASE WHEN ProficiencyLevel = 'Expert' THEN 1 END) as expert_skills,
                COUNT(CASE WHEN ProficiencyLevel = 'Advanced' THEN 1 END) as advanced_skills
            FROM UserSkills 
            WHERE UserID = ?
        """
        cursor.execute(stats_query, (profile_id,))
        stats = cursor.fetchone()
        
        skill_stats = {
            'total_skills': stats[0] if stats else 0,
            'verified_skills': stats[1] if stats else 0,
            'expert_skills': stats[2] if stats else 0,
            'advanced_skills': stats[3] if stats else 0
        }
        
        # Get user reviews if viewing someone else's profile
        reviews = []
        if not is_own_profile:
            reviews_query = """
                SELECT r.*, u.Username as ReviewerUsername, t.StartDate
                FROM Reviews r
                JOIN Users u ON r.ReviewerUserID = u.UserID
                JOIN Transactions t ON r.TransactionID = t.TransactionID
                WHERE r.ReceiverUserID = ?
                ORDER BY r.CreatedDate DESC
            """
            cursor.execute(reviews_query, (profile_id,))
            reviews = cursor.fetchall()
        
        conn.close()
        
        return render_template('profile.html', 
                             user=user_dict, 
                             skills=user_skills, 
                             skill_stats=skill_stats,
                             reviews=reviews,
                             is_own_profile=is_own_profile)
        
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    if 'user_id' not in session:
        flash('Please log in to edit your profile.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Security check: Ensure user can only edit their own profile
    profile_id = request.form.get('profile_id')
    if profile_id and str(profile_id) != str(user_id):
        flash('Unauthorized: You can only edit your own profile.', 'error')
        return redirect(url_for('profile'))
    
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    bio = request.form.get('bio')
    location = request.form.get('location')
    
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('profile'))
            
        cursor = conn.cursor()
        
        update_query = """
            UPDATE Users 
            SET FirstName = ?, LastName = ?, Bio = ?, Location = ?
            WHERE UserID = ?
        """
        cursor.execute(update_query, (first_name, last_name, bio, location, user_id))
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'error')
        return redirect(url_for('profile'))

# FIXED: Add skill route that accepts both GET and POST methods
@app.route('/add_skill', methods=['GET', 'POST'])
@login_required
def add_skill():
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Security check: Ensure user can only add skills to their own profile
        profile_id = request.form.get('profile_id')
        if profile_id and str(profile_id) != str(user_id):
            flash('Unauthorized: You can only add skills to your own profile.', 'error')
            return redirect(url_for('profile'))
        
        skill_id = request.form.get('skill_id')
        proficiency_level = request.form.get('proficiency_level')
        years_experience = request.form.get('years_experience', 0)
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Database connection error. Please try again later.', 'error')
                return redirect(url_for('profile'))
                
            cursor = conn.cursor()
            
            # Check if user already has this skill
            check_query = "SELECT UserSkillID FROM UserSkills WHERE UserID = ? AND SkillID = ?"
            cursor.execute(check_query, (user_id, skill_id))
            existing_skill = cursor.fetchone()
            
            if existing_skill:
                flash('You already have this skill in your profile.', 'warning')
            else:
                # Add new skill
                insert_query = """
                    INSERT INTO UserSkills (UserID, SkillID, ProficiencyLevel, YearsExperience, IsVerified, CreatedDate)
                    VALUES (?, ?, ?, ?, 0, GETDATE())
                """
                cursor.execute(insert_query, (user_id, skill_id, proficiency_level, years_experience))
                conn.commit()
                flash('Skill added successfully!', 'success')
            
            conn.close()
            
        except Exception as e:
            flash(f'Error adding skill: {str(e)}', 'error')
        
        return redirect(url_for('profile'))
    
    # GET request - show the add skill form
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    # Get all skills
    cursor.execute("""
        SELECT s.*, c.CategoryName
        FROM Skills s
        JOIN Categories c ON s.CategoryID = c.CategoryID
        WHERE s.IsActive = 1
        ORDER BY c.CategoryName, s.SkillName
    """)
    skills = cursor.fetchall()
    
    conn.close()
    
    return render_template('add_skill.html', skills=skills)

@app.route('/remove_skill/<int:user_skill_id>')
@login_required
def remove_skill(user_skill_id):
    if 'user_id' not in session:
        flash('Please log in to remove skills.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('profile'))
            
        cursor = conn.cursor()
        
        # Security check: Verify the skill belongs to the current user
        verify_query = "SELECT UserID FROM UserSkills WHERE UserSkillID = ?"
        cursor.execute(verify_query, (user_skill_id,))
        skill_owner = cursor.fetchone()
        
        if not skill_owner:
            flash('Skill not found.', 'error')
        elif skill_owner[0] != user_id:
            flash('Unauthorized: You can only remove your own skills.', 'error')
        else:
            delete_query = "DELETE FROM UserSkills WHERE UserSkillID = ?"
            cursor.execute(delete_query, (user_skill_id,))
            conn.commit()
            flash('Skill removed successfully!', 'success')
        
        conn.close()
        
    except Exception as e:
        flash(f'Error removing skill: {str(e)}', 'error')
    
    return redirect(url_for('profile'))

@app.route('/get_skills')
@login_required
def get_skills():
    # This endpoint is only for authenticated users to get skills for their own profile
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection error'})
            
        cursor = conn.cursor()
        
        skills_query = """
            SELECT s.SkillID, s.SkillName, COALESCE(c.CategoryName, 'General') as Category 
            FROM Skills s 
            LEFT JOIN Categories c ON s.CategoryID = c.CategoryID 
            WHERE s.IsActive = 1 
            ORDER BY Category, s.SkillName
        """
        cursor.execute(skills_query)
        skills_rows = cursor.fetchall()
        
        skills_list = []
        for skill in skills_rows:
            skills_list.append({
                'SkillID': skill[0],
                'SkillName': skill[1],
                'Category': skill[2]
            })
        
        conn.close()
        return jsonify({'skills': skills_list})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile_page():
    user_id = session['user_id']
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        bio = request.form['bio']
        location = request.form['location']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('edit_profile.html')
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE Users
                SET FirstName = ?, LastName = ?, Bio = ?, Location = ?
                WHERE UserID = ?
            """, (first_name, last_name, bio, location, user_id))
            conn.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            conn.close()
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE UserID = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return render_template('edit_profile.html', user=user)

@app.route('/skills')
def browse_skills():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    # Get all categories
    cursor.execute("SELECT * FROM Categories ORDER BY CategoryName")
    categories = cursor.fetchall()
    
    # Get skills with category info
    cursor.execute("""
        SELECT s.*, c.CategoryName
        FROM Skills s
        JOIN Categories c ON s.CategoryID = c.CategoryID
        WHERE s.IsActive = 1
        ORDER BY c.CategoryName, s.SkillName
    """)
    skills = cursor.fetchall()
    
    conn.close()
    
    return render_template('browse_skills.html', categories=categories, skills=skills)

@app.route('/skills/<int:skill_id>')
def skill_detail(skill_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('browse_skills'))
        
    cursor = conn.cursor()
    
    # Get skill details
    cursor.execute("""
        SELECT s.*, c.CategoryName
        FROM Skills s
        JOIN Categories c ON s.CategoryID = c.CategoryID
        WHERE s.SkillID = ?
    """, (skill_id,))
    skill = cursor.fetchone()
    
    if not skill:
        flash('Skill not found', 'error')
        return redirect(url_for('browse_skills'))
    
    # Get users with this skill
    cursor.execute("""
        SELECT u.UserID, u.Username, u.FirstName, u.LastName, u.ReputationScore, us.ProficiencyLevel
        FROM Users u
        JOIN UserSkills us ON u.UserID = us.UserID
        WHERE us.SkillID = ? AND u.IsActive = 1
        ORDER BY us.ProficiencyLevel DESC, u.ReputationScore DESC
    """, (skill_id,))
    users = cursor.fetchall()
    
    conn.close()
    
    return render_template('skill_detail.html', skill=skill, users=users)

@app.route('/create_request', methods=['GET', 'POST'])
@login_required
def create_request():
    user_id = session['user_id']
    
    if request.method == 'POST':
        skill_id = request.form['skill_id']
        proficiency = request.form['proficiency']
        description = request.form['description']
        is_urgent = 'is_urgent' in request.form
        expiry_days = int(request.form['expiry_days'])
        
        expiry_date = datetime.now() + timedelta(days=expiry_days)
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('create_request.html')
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO SkillRequests (UserID, SkillID, DesiredProficiencyLevel, Description, IsUrgent, CreatedDate, ExpiryDate, Status)
                VALUES (?, ?, ?, ?, ?, GETDATE(), ?, 'Open')
            """, (user_id, skill_id, proficiency, description, is_urgent, expiry_date))
            conn.commit()
            
            flash('Skill request created successfully', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            conn.close()
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    # Get all skills
    cursor.execute("""
        SELECT s.*, c.CategoryName
        FROM Skills s
        JOIN Categories c ON s.CategoryID = c.CategoryID
        WHERE s.IsActive = 1
        ORDER BY c.CategoryName, s.SkillName
    """)
    skills = cursor.fetchall()
    
    conn.close()
    
    return render_template('create_request.html', skills=skills)

@app.route('/browse_requests')
def browse_requests():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    # Get open requests
    cursor.execute("""
        SELECT sr.*, s.SkillName, u.Username, u.Location, u.ReputationScore
        FROM SkillRequests sr
        JOIN Skills s ON sr.SkillID = s.SkillID
        JOIN Users u ON sr.UserID = u.UserID
        WHERE sr.Status = 'Open' AND sr.ExpiryDate > GETDATE()
        ORDER BY sr.IsUrgent DESC, sr.CreatedDate DESC
    """)
    requests = cursor.fetchall()
    
    conn.close()
    
    return render_template('browse_requests.html', requests=requests)

@app.route('/request/<int:request_id>')
def request_detail(request_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('browse_requests'))
        
    cursor = conn.cursor()
    
    # Get request details
    cursor.execute("""
        SELECT sr.*, s.SkillName, c.CategoryName, u.Username, u.FirstName, u.LastName, u.Location, u.ReputationScore
        FROM SkillRequests sr
        JOIN Skills s ON sr.SkillID = s.SkillID
        JOIN Categories c ON s.CategoryID = c.CategoryID
        JOIN Users u ON sr.UserID = u.UserID
        WHERE sr.RequestID = ?
    """, (request_id,))
    request_data = cursor.fetchone()
    
    if not request_data:
        flash('Request not found', 'error')
        return redirect(url_for('browse_requests'))
    
    # Check if current user has the requested skill
    can_offer_help = False
    if 'user_id' in session:
        cursor.execute("""
            SELECT UserSkillID, ProficiencyLevel
            FROM UserSkills
            WHERE UserID = ? AND SkillID = ?
        """, (session['user_id'], request_data.SkillID))
        user_skill = cursor.fetchone()
        
        if user_skill:
            can_offer_help = True
    
    conn.close()
    
    return render_template('request_detail.html', request=request_data, can_offer_help=can_offer_help)

@app.route('/offer_help/<int:request_id>', methods=['POST'])
@login_required
def offer_help(request_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('request_detail', request_id=request_id))
        
    cursor = conn.cursor()
    
    try:
        # Get request details
        cursor.execute("SELECT UserID, SkillID, Status FROM SkillRequests WHERE RequestID = ?", (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            flash('Request not found', 'error')
            return redirect(url_for('browse_requests'))
        
        if request_data.Status != 'Open':
            flash('This request is no longer open', 'error')
            return redirect(url_for('request_detail', request_id=request_id))
        
        if request_data.UserID == user_id:
            flash('You cannot offer help on your own request', 'error')
            return redirect(url_for('request_detail', request_id=request_id))
        
        # Check if user has the skill
        cursor.execute("SELECT UserSkillID FROM UserSkills WHERE UserID = ? AND SkillID = ?", (user_id, request_data.SkillID))
        user_skill = cursor.fetchone()
        
        if not user_skill:
            flash('You do not have the required skill', 'error')
            return redirect(url_for('request_detail', request_id=request_id))
        
        # Create a match
        cursor.execute("""
            EXEC MatchUsers @RequestID = ?, @ProviderUserID = ?
        """, (request_id, user_id))
        conn.commit()
        
        flash('You have offered to help with this request', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('request_detail', request_id=request_id))

# FIXED: Accept match route - bypasses problematic stored procedure
@app.route('/accept_match/<int:match_id>', methods=['POST'])
@login_required
def accept_match(match_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    cursor = conn.cursor()
    
    try:
        # Get match details and verify user is the requestor
        cursor.execute("""
            SELECT m.MatchID, m.RequestorUserID, m.ProviderUserID, m.Status, m.RequestID,
                   sr.UserID as RequestCreatorID, sr.SkillID, s.SkillName,
                   u1.Username as RequestorUsername, u2.Username as ProviderUsername
            FROM Matches m
            JOIN SkillRequests sr ON m.RequestID = sr.RequestID
            JOIN Skills s ON sr.SkillID = s.SkillID
            JOIN Users u1 ON m.RequestorUserID = u1.UserID
            JOIN Users u2 ON m.ProviderUserID = u2.UserID
            WHERE m.MatchID = ?
        """, (match_id,))
        
        match_data = cursor.fetchone()
        
        if not match_data:
            flash('Match not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Verify that the current user is the requestor (who created the original skill request)
        if match_data.RequestorUserID != user_id:
            flash('You can only accept matches for your own requests', 'error')
            return redirect(url_for('dashboard'))
        
        # Verify match is still pending
        if match_data.Status != 'Pending':
            flash('This match has already been processed', 'error')
            return redirect(url_for('dashboard'))
        
        # Update match status directly (bypassing the problematic stored procedure)
        cursor.execute("""
            UPDATE Matches 
            SET Status = 'Accepted'
            WHERE MatchID = ?
        """, (match_id,))
        
        # Update the original skill request status to 'Matched'
        cursor.execute("""
            UPDATE SkillRequests 
            SET Status = 'Matched'
            WHERE RequestID = ?
        """, (match_data.RequestID,))
        
        # Create notifications for both users
        # Notification for the provider
        cursor.execute("""
            INSERT INTO Notifications (UserID, Type, Message, IsRead, CreatedDate)
            VALUES (?, 'MatchAccepted', ?, 0, GETDATE())
        """, (match_data.ProviderUserID, 
              f'Your offer to help with {match_data.SkillName} has been accepted by {match_data.RequestorUsername}!'))
        
        # Notification for the requestor (confirmation)
        cursor.execute("""
            INSERT INTO Notifications (UserID, Type, Message, IsRead, CreatedDate)
            VALUES (?, 'MatchAccepted', ?, 0, GETDATE())
        """, (match_data.RequestorUserID, 
              f'You have accepted {match_data.ProviderUsername}\'s offer to help with {match_data.SkillName}!'))
        
        conn.commit()
        
        flash(f'Match accepted successfully! You can now schedule a session with {match_data.ProviderUsername}.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred while accepting the match: {str(e)}', 'error')
        print(f"Error in accept_match: {str(e)}")
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

def convert_datetime_string(datetime_str):
    """Convert HTML datetime-local string to SQL Server compatible datetime"""
    try:
        # Parse the datetime string from HTML input (format: YYYY-MM-DDTHH:MM)
        dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        # Return in SQL Server compatible format
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Error parsing datetime: {e}")
        return None

# UPDATED: Schedule transaction route - redirects to active transaction page
@app.route('/schedule_transaction/<int:match_id>', methods=['GET', 'POST'])
@login_required
def schedule_transaction(match_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    cursor = conn.cursor()
    
    # Check if user is part of this match
    cursor.execute("""
        SELECT m.*, u1.Username as RequestorUsername, u2.Username as ProviderUsername
        FROM Matches m
        JOIN Users u1 ON m.RequestorUserID = u1.UserID
        JOIN Users u2 ON m.ProviderUserID = u2.UserID
        WHERE m.MatchID = ? AND (m.RequestorUserID = ? OR m.ProviderUserID = ?)
    """, (match_id, user_id, user_id))
    match_data = cursor.fetchone()
    
    if not match_data:
        flash('Match not found or you are not authorized', 'error')
        return redirect(url_for('dashboard'))
    
    if match_data.Status != 'Accepted':
        flash('This match is not in Accepted status', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        start_date_raw = request.form['start_date']
        end_date_raw = request.form['end_date']
        notes = request.form['notes']
        
        try:
            # Convert HTML datetime-local format to SQL Server compatible format
            start_dt = datetime.strptime(start_date_raw, '%Y-%m-%dT%H:%M')
            start_date = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            end_dt = datetime.strptime(end_date_raw, '%Y-%m-%dT%H:%M')
            end_date = end_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Validate that end date is after start date
            if end_dt <= start_dt:
                flash('End time must be after start time.', 'error')
                return render_template('schedule_transaction.html', match=match_data)
            
            # Validate that the session is not in the past
            if start_dt <= datetime.now():
                flash('Start time must be in the future.', 'error')
                return render_template('schedule_transaction.html', match=match_data)
            
            # Execute the stored procedure with converted datetime strings
            cursor.execute("""
                EXEC CreateSkillSwapTransaction @MatchID = ?, @StartDate = ?, @EndDate = ?, @Notes = ?
            """, (match_id, start_date, end_date, notes))
            
            # Get the transaction ID that was just created
            cursor.execute("""
                SELECT TOP 1 TransactionID 
                FROM Transactions 
                WHERE MatchID = ? 
                ORDER BY CreatedDate DESC
            """, (match_id,))
            transaction_result = cursor.fetchone()
            
            conn.commit()
            
            if transaction_result:
                transaction_id = transaction_result[0]
                flash('Transaction scheduled successfully', 'success')
                # Redirect to the active transaction page
                return redirect(url_for('active_transaction', transaction_id=transaction_id))
            else:
                flash('Transaction created but could not retrieve details', 'warning')
                return redirect(url_for('dashboard'))
            
        except ValueError as ve:
            print(f"Date parsing error: {ve}")
            flash('Invalid date format. Please check your date and time inputs.', 'error')
            return render_template('schedule_transaction.html', match=match_data)
        except Exception as e:
            print(f"Database error: {str(e)}")
            flash(f'An error occurred while scheduling: Please try again.', 'error')
            return render_template('schedule_transaction.html', match=match_data)
    
    conn.close()
    
    return render_template('schedule_transaction.html', match=match_data)

# NEW: Active transaction route
@app.route('/active_transaction/<int:transaction_id>')
@login_required
def active_transaction(transaction_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    cursor = conn.cursor()
    
    # Get transaction details with user and skill information
    cursor.execute("""
        SELECT 
            t.*,
            m.RequestorUserID, m.ProviderUserID,
            u1.Username as RequestorUsername, u1.FirstName as RequestorFirstName, 
            u1.LastName as RequestorLastName, u1.Email as RequestorEmail,
            u1.Location as RequestorLocation, u1.ReputationScore as RequestorReputation,
            u2.Username as ProviderUsername, u2.FirstName as ProviderFirstName,
            u2.LastName as ProviderLastName, u2.Email as ProviderEmail,
            u2.Location as ProviderLocation, u2.ReputationScore as ProviderReputation,
            s.SkillName, s.Description as SkillDescription,
            c.CategoryName,
            sr.DesiredProficiencyLevel, sr.Description as RequestDescription,
            us.ProficiencyLevel as ProviderProficiency, us.YearsExperience as ProviderExperience
        FROM Transactions t
        JOIN Matches m ON t.MatchID = m.MatchID
        JOIN SkillRequests sr ON m.RequestID = sr.RequestID
        JOIN Skills s ON sr.SkillID = s.SkillID
        JOIN Categories c ON s.CategoryID = c.CategoryID
        JOIN Users u1 ON m.RequestorUserID = u1.UserID
        JOIN Users u2 ON m.ProviderUserID = u2.UserID
        LEFT JOIN UserSkills us ON (us.UserID = m.ProviderUserID AND us.SkillID = s.SkillID)
        WHERE t.TransactionID = ? AND (m.RequestorUserID = ? OR m.ProviderUserID = ?)
    """, (transaction_id, user_id, user_id))
    
    transaction = cursor.fetchone()
    
    if not transaction:
        flash('Transaction not found or you are not authorized to view it', 'error')
        return redirect(url_for('dashboard'))
    
    # Determine current user's role
    is_requestor = transaction.RequestorUserID == user_id
    other_user_id = transaction.ProviderUserID if is_requestor else transaction.RequestorUserID
    
    # Check if transaction can be completed (past end date)
    can_complete = datetime.now() >= transaction.EndDate if transaction.EndDate else False
    
    # Check if already reviewed
    cursor.execute("""
        SELECT ReviewID
        FROM Reviews
        WHERE TransactionID = ? AND ReviewerUserID = ?
    """, (transaction_id, user_id))
    has_reviewed = cursor.fetchone() is not None
    
    conn.close()
    
    return render_template('active_transaction.html', 
                         transaction=transaction,
                         is_requestor=is_requestor,
                         other_user_id=other_user_id,
                         can_complete=can_complete,
                         has_reviewed=has_reviewed)

# NEW: Complete transaction route
@app.route('/complete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def complete_transaction(transaction_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('active_transaction', transaction_id=transaction_id))
        
    cursor = conn.cursor()
    
    try:
        # Verify user is part of this transaction
        cursor.execute("""
            SELECT m.RequestorUserID, m.ProviderUserID, t.Status, t.EndDate
            FROM Transactions t
            JOIN Matches m ON t.MatchID = m.MatchID
            WHERE t.TransactionID = ?
        """, (transaction_id,))
        
        transaction_data = cursor.fetchone()
        
        if not transaction_data:
            flash('Transaction not found', 'error')
            return redirect(url_for('dashboard'))
        
        if user_id not in [transaction_data.RequestorUserID, transaction_data.ProviderUserID]:
            flash('You are not authorized to complete this transaction', 'error')
            return redirect(url_for('dashboard'))
        
        if transaction_data.Status == 'Completed':
            flash('This transaction is already completed', 'info')
            return redirect(url_for('active_transaction', transaction_id=transaction_id))
        
        # Check if transaction end date has passed
        if datetime.now() < transaction_data.EndDate:
            flash('Transaction cannot be completed before the scheduled end time', 'error')
            return redirect(url_for('active_transaction', transaction_id=transaction_id))
        
        # Update transaction status
        cursor.execute("""
            UPDATE Transactions
            SET Status = 'Completed', CompletedDate = GETDATE()
            WHERE TransactionID = ?
        """, (transaction_id,))
        
        conn.commit()
        flash('Transaction completed successfully! You can now leave a review.', 'success')
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('active_transaction', transaction_id=transaction_id))

# UPDATED: Messages route with notification clearing
@app.route('/messages')
@login_required
def messages():
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    cursor = conn.cursor()
    
    # Mark all messages as read when user opens messages page
    cursor.execute("""
        UPDATE Messages
        SET IsRead = 1, ReadDate = GETDATE()
        WHERE ReceiverUserID = ? AND IsRead = 0
    """, (user_id,))
    conn.commit()
    
    # First, get distinct other user IDs
    cursor.execute("""
        SELECT DISTINCT
            CASE 
                WHEN SenderUserID = ? THEN ReceiverUserID
                ELSE SenderUserID
            END AS OtherUserID
        FROM Messages
        WHERE SenderUserID = ? OR ReceiverUserID = ?
    """, (user_id, user_id, user_id))
    
    other_user_ids = [row.OtherUserID for row in cursor.fetchall()]
    
    # If there are no conversations, return empty list
    if not other_user_ids:
        return render_template('messages.html', conversations=[])
    
    # Now get the details for each conversation
    conversations = []
    for other_id in other_user_ids:
        # Get user details
        cursor.execute("""
            SELECT UserID, Username, FirstName, LastName, ProfilePicture
            FROM Users
            WHERE UserID = ?
        """, (other_id,))
        user_details = cursor.fetchone()
        
        # Get last message date and content
        cursor.execute("""
            SELECT TOP 1 SentDate, MessageContent, SenderUserID
            FROM Messages
            WHERE (SenderUserID = ? AND ReceiverUserID = ?)
               OR (SenderUserID = ? AND ReceiverUserID = ?)
            ORDER BY SentDate DESC
        """, (user_id, other_id, other_id, user_id))
        last_message = cursor.fetchone()
        
        # Get unread count for this conversation
        cursor.execute("""
            SELECT COUNT(*) as unread_count
            FROM Messages
            WHERE SenderUserID = ? AND ReceiverUserID = ? AND IsRead = 0
        """, (other_id, user_id))
        unread_result = cursor.fetchone()
        unread_count = unread_result[0] if unread_result else 0
        
        if user_details and last_message:
            conversation = {
                'OtherUserID': other_id,
                'Username': user_details.Username,
                'FirstName': user_details.FirstName,
                'LastName': user_details.LastName,
                'ProfilePicture': user_details.ProfilePicture,
                'LastMessageDate': last_message.SentDate,
                'LastMessageContent': last_message.MessageContent[:50] + '...' if len(last_message.MessageContent) > 50 else last_message.MessageContent,
                'LastMessageFromMe': last_message.SenderUserID == user_id,
                'UnreadCount': unread_count
            }
            conversations.append(conversation)
    
    # Sort by last message date
    conversations.sort(key=lambda x: x['LastMessageDate'], reverse=True)
    
    conn.close()
    
    return render_template('messages.html', conversations=conversations)
    
@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    cursor = conn.cursor()
    
    # Get all notifications
    try:
        cursor.execute("""
            SELECT *
            FROM Notifications
            WHERE UserID = ?
            ORDER BY CreatedDate DESC
        """, (user_id,))
        notifications = cursor.fetchall()
    except:
        # If CreatedDate doesn't exist, try without ORDER BY
        cursor.execute("""
            SELECT *
            FROM Notifications
            WHERE UserID = ?
        """, (user_id,))
        notifications = cursor.fetchall()
    
    # Mark all as read
    cursor.execute("""
        UPDATE Notifications
        SET IsRead = 1, ReadDate = GETDATE()
        WHERE UserID = ? AND IsRead = 0
    """, (user_id,))
    conn.commit()
    
    conn.close()
    
    return render_template('notifications.html', notifications=notifications)

@app.route('/leave_review/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def leave_review(transaction_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    cursor = conn.cursor()
    
    # Get transaction details
    cursor.execute("""
        SELECT t.*, m.RequestorUserID, m.ProviderUserID, 
            u1.Username as RequestorUsername, u2.Username as ProviderUsername
        FROM Transactions t
        JOIN Matches m ON t.MatchID = m.MatchID
        JOIN Users u1 ON m.RequestorUserID = u1.UserID
        JOIN Users u2 ON m.ProviderUserID = u2.UserID
        WHERE t.TransactionID = ? AND (m.RequestorUserID = ? OR m.ProviderUserID = ?)
    """, (transaction_id, user_id, user_id))
    transaction = cursor.fetchone()
    
    if not transaction:
        flash('Transaction not found or you are not authorized', 'error')
        return redirect(url_for('dashboard'))
    
    # Determine who to review
    if transaction.RequestorUserID == user_id:
        receiver_id = transaction.ProviderUserID
        receiver_username = transaction.ProviderUsername
    else:
        receiver_id = transaction.RequestorUserID
        receiver_username = transaction.RequestorUsername
    
    # Check if already reviewed
    cursor.execute("""
        SELECT ReviewID
        FROM Reviews
        WHERE TransactionID = ? AND ReviewerUserID = ? AND ReceiverUserID = ?
    """, (transaction_id, user_id, receiver_id))
    existing_review = cursor.fetchone()
    
    if existing_review:
        flash('You have already reviewed this transaction', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        rating = request.form['rating']
        comment = request.form['comment']
        
        try:
            cursor.execute("""
                INSERT INTO Reviews (TransactionID, ReviewerUserID, ReceiverUserID, Rating, Comment, CreatedDate)
                VALUES (?, ?, ?, ?, ?, GETDATE())
            """, (transaction_id, user_id, receiver_id, rating, comment))
            conn.commit()
            
            flash('Review submitted successfully', 'success')
            return redirect(url_for('active_transaction', transaction_id=transaction_id))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
    
    conn.close()
    
    return render_template('leave_review.html', transaction=transaction, receiver_username=receiver_username)

# Add explicit routes for static pages
@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/community_guidelines')
def community_guidelines():
    return render_template('community_guidelines.html')

@app.route('/how_it_works')
def how_it_works():
    return render_template('how_it_works.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')

# UPDATED: Conversation route with notification clearing
@app.route('/conversation/<int:other_user_id>')
@login_required
def conversation(other_user_id):
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    cursor = conn.cursor()
    
    # Get other user details
    cursor.execute("""
        SELECT UserID, Username, FirstName, LastName, ProfilePicture
        FROM Users
        WHERE UserID = ?
    """, (other_user_id,))
    other_user = cursor.fetchone()
    
    if not other_user:
        flash('User not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Mark messages as read from this specific user
    cursor.execute("""
        UPDATE Messages
        SET IsRead = 1, ReadDate = GETDATE()
        WHERE SenderUserID = ? AND ReceiverUserID = ? AND IsRead = 0
    """, (other_user_id, user_id))
    conn.commit()
    
    # Get conversation history
    cursor.execute("""
        SELECT *
        FROM Messages
        WHERE (SenderUserID = ? AND ReceiverUserID = ?)
           OR (SenderUserID = ? AND ReceiverUserID = ?)
        ORDER BY SentDate ASC
    """, (user_id, other_user_id, other_user_id, user_id))
    messages = cursor.fetchall()
    
    conn.close()
    
    return render_template('conversation.html', other_user=other_user, messages=messages)

# NEW: API endpoint for message notification count
@app.route('/api/notifications/messages/count', methods=['GET'])
@login_required
def api_get_unread_messages_count():
    if 'user_id' not in session:
        return jsonify({'count': 0}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'count': 0, 'error': 'Database connection error'}), 500
        
        cursor = conn.cursor()
        
        # Get unread messages count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM Messages
            WHERE ReceiverUserID = ? AND IsRead = 0
        """, (session['user_id'],))
        
        result = cursor.fetchone()
        count = result[0] if result else 0
        
        return jsonify({'count': count})
    
    except Exception as e:
        return jsonify({'count': 0, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# UPDATED: Send message API with notification updates
@app.route('/api/messages/send', methods=['POST'])
def api_send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
            
        sender_id = session['user_id']
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        if not receiver_id:
            return jsonify({'success': False, 'error': 'Missing receiver_id'}), 400
        
        if not content or not content.strip():
            return jsonify({'success': False, 'error': 'Message content cannot be empty'}), 400
        
        # Convert receiver_id to int if it's a string
        if isinstance(receiver_id, str):
            try:
                receiver_id = int(receiver_id)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid receiver_id format'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection error'}), 500
        
        cursor = conn.cursor()
        
        # Check if receiver exists
        cursor.execute("SELECT UserID FROM Users WHERE UserID = ?", (receiver_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        # Insert message
        try:
            cursor.execute("""
                INSERT INTO Messages (SenderUserID, ReceiverUserID, MessageContent, SentDate, IsRead)
                VALUES (?, ?, ?, GETDATE(), 0)
            """, (sender_id, receiver_id, content))
            
            cursor.execute("SELECT @@IDENTITY AS ID")
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'success': False, 'error': 'Failed to get message ID'}), 500
                
            message_id = int(result[0])
            conn.commit()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get updated unread count for receiver
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM Messages
                WHERE ReceiverUserID = ? AND IsRead = 0
            """, (receiver_id,))
            unread_result = cursor.fetchone()
            unread_count = unread_result[0] if unread_result else 0
            
            # Emit message data
            message_data = {
                'id': message_id,
                'sender_id': str(sender_id),
                'receiver_id': str(receiver_id),
                'content': content,
                'sent_date': current_time
            }
            
            # Emit notification update to receiver
            notification_data = {
                'type': 'message_notification',
                'unread_count': unread_count,
                'sender_id': str(sender_id)
            }
            
            # Emit to receiver
            socketio.emit('new_message', message_data, room=f'user_{receiver_id}')
            socketio.emit('notification_update', notification_data, room=f'user_{receiver_id}')
            
            # Also emit to the sender
            socketio.emit('new_message', message_data, room=f'user_{sender_id}')
            
            return jsonify({
                'success': True, 
                'message_id': message_id,
                'sent_date': current_time
            })
            
        except Exception as e:
            conn.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/messages/<int:message_id>/read', methods=['POST'])
def api_mark_message_read(message_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection error'}), 500
        
        cursor = conn.cursor()
        
        # Mark message as read
        cursor.execute("""
            UPDATE Messages
            SET IsRead = 1, ReadDate = GETDATE()
            WHERE MessageID = ? AND ReceiverUserID = ?
        """, (message_id, session['user_id']))
        conn.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/messages/unread/count', methods=['GET'])
def api_get_unread_count():
    if 'user_id' not in session:
        return jsonify({'count': 0}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'count': 0, 'error': 'Database connection error'}), 500
        
        cursor = conn.cursor()
        
        # Get unread count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM Messages
            WHERE ReceiverUserID = ? AND IsRead = 0
        """, (session['user_id'],))
        
        result = cursor.fetchone()
        count = result[0] if result else 0
        
        return jsonify({'count': count})
    
    except Exception as e:
        return jsonify({'count': 0, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Debug routes
@app.route('/debug/socket-test')
def socket_test():
    return render_template('socket_test.html')

@app.route('/api/debug/emit-test', methods=['POST'])
def emit_test():
    data = request.json
    room = data.get('room')
    message = data.get('message', 'Test message')
    
    if not room:
        return jsonify({'success': False, 'error': 'Room is required'}), 400
    
    socketio.emit('test_message', {
        'message': message,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)
    
    return jsonify({'success': True, 'message': f'Message sent to room {room}'})

# Add a route for testing database connection
@app.route('/test-db')
def test_db_route():
    if test_db_connection():
        return jsonify({'status': 'success', 'message': 'Database connection successful'})
    else:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

# Add error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash):
    return hashlib.sha256(password.encode()).hexdigest() == hash

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print("Client connected to Socket.IO")
    if 'user_id' in session:
        user_id = session['user_id']
        join_room(f'user_{user_id}')
        print(f"User {user_id} connected and joined room user_{user_id}")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected from Socket.IO")
    if 'user_id' in session:
        user_id = session['user_id']
        leave_room(f'user_{user_id}')
        print(f"User {user_id} disconnected and left room user_{user_id}")

@socketio.on('join')
def handle_join(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(f'user_{user_id}')
        print(f"User {user_id} joined room user_{user_id}")
        # Acknowledge the join
        emit('joined', {'status': 'success', 'room': f'user_{user_id}'})

# Add typing indicator functionality
@socketio.on('typing')
def handle_typing(data):
    user_id = data.get('user_id')
    receiver_id = data.get('receiver_id')
    
    if user_id and receiver_id:
        print(f"User {user_id} is typing to {receiver_id}")
        socketio.emit('typing', {
            'user_id': user_id
        }, room=f'user_{receiver_id}')

if __name__ == '__main__':
    # Check database connection on startup
    if not test_db_connection():
        print("WARNING: Database connection failed on startup!")
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)