-- MySQL Database Schema for SkillSwap Application
-- Run this script in your PythonAnywhere MySQL console

-- Create Users table
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
    LastActive DATETIME DEFAULT CURRENT_TIMESTAMP,
    ProfilePicture VARCHAR(255)
);

-- Create Categories table
CREATE TABLE Categories (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL UNIQUE,
    Description TEXT,
    IsActive BOOLEAN DEFAULT TRUE
);

-- Create Skills table
CREATE TABLE Skills (
    SkillID INT AUTO_INCREMENT PRIMARY KEY,
    SkillName VARCHAR(100) NOT NULL,
    Description TEXT,
    CategoryID INT,
    IsActive BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
);

-- Create UserSkills table
CREATE TABLE UserSkills (
    UserSkillID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    SkillID INT NOT NULL,
    ProficiencyLevel ENUM('Beginner', 'Intermediate', 'Advanced', 'Expert') DEFAULT 'Beginner',
    YearsExperience INT DEFAULT 0,
    IsVerified BOOLEAN DEFAULT FALSE,
    VerificationDate DATETIME,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (SkillID) REFERENCES Skills(SkillID) ON DELETE CASCADE,
    UNIQUE KEY unique_user_skill (UserID, SkillID)
);

-- Create SkillRequests table
CREATE TABLE SkillRequests (
    RequestID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    SkillID INT NOT NULL,
    DesiredProficiencyLevel ENUM('Beginner', 'Intermediate', 'Advanced', 'Expert') DEFAULT 'Beginner',
    Description TEXT,
    IsUrgent BOOLEAN DEFAULT FALSE,
    Status ENUM('Open', 'Matched', 'Completed', 'Expired') DEFAULT 'Open',
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    ExpiryDate DATETIME,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (SkillID) REFERENCES Skills(SkillID) ON DELETE CASCADE
);

-- Create Matches table
CREATE TABLE Matches (
    MatchID INT AUTO_INCREMENT PRIMARY KEY,
    RequestID INT NOT NULL,
    ProviderUserID INT NOT NULL,
    RequestorUserID INT NOT NULL,
    Status ENUM('Pending', 'Accepted', 'Rejected', 'Cancelled') DEFAULT 'Pending',
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (RequestID) REFERENCES SkillRequests(RequestID) ON DELETE CASCADE,
    FOREIGN KEY (ProviderUserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (RequestorUserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Create Transactions table
CREATE TABLE Transactions (
    TransactionID INT AUTO_INCREMENT PRIMARY KEY,
    MatchID INT NOT NULL,
    StartDate DATETIME NOT NULL,
    EndDate DATETIME NOT NULL,
    Status ENUM('Scheduled', 'Active', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    Notes TEXT,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    CompletedDate DATETIME,
    FOREIGN KEY (MatchID) REFERENCES Matches(MatchID) ON DELETE CASCADE
);

-- Create Messages table
CREATE TABLE Messages (
    MessageID INT AUTO_INCREMENT PRIMARY KEY,
    SenderUserID INT NOT NULL,
    ReceiverUserID INT NOT NULL,
    MessageContent TEXT NOT NULL,
    SentDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    ReadDate DATETIME,
    IsRead BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (SenderUserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ReceiverUserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Create Reviews table
CREATE TABLE Reviews (
    ReviewID INT AUTO_INCREMENT PRIMARY KEY,
    TransactionID INT NOT NULL,
    ReviewerUserID INT NOT NULL,
    ReceiverUserID INT NOT NULL,
    Rating INT CHECK (Rating >= 1 AND Rating <= 5),
    Comment TEXT,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID) ON DELETE CASCADE,
    FOREIGN KEY (ReviewerUserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ReceiverUserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Create Notifications table
CREATE TABLE Notifications (
    NotificationID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Type ENUM('MatchAccepted', 'NewMessage', 'ReviewReceived', 'TransactionScheduled', 'System') DEFAULT 'System',
    Message TEXT NOT NULL,
    IsRead BOOLEAN DEFAULT FALSE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    ReadDate DATETIME,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Insert sample categories
INSERT INTO Categories (CategoryName, Description) VALUES
('Programming', 'Software development and programming languages'),
('Design', 'Graphic design, UI/UX, and creative skills'),
('Marketing', 'Digital marketing, social media, and advertising'),
('Business', 'Business management and entrepreneurship'),
('Language', 'Language learning and translation'),
('Music', 'Musical instruments and music production'),
('Art', 'Drawing, painting, and visual arts'),
('Cooking', 'Culinary skills and recipe sharing'),
('Sports', 'Physical activities and sports training'),
('Technology', 'IT support and technical skills');

-- Insert sample skills
INSERT INTO Skills (SkillName, Description, CategoryID) VALUES
('Python Programming', 'Python programming language', 1),
('JavaScript', 'JavaScript programming language', 1),
('React.js', 'React JavaScript library', 1),
('Graphic Design', 'Visual design and graphics', 2),
('UI/UX Design', 'User interface and experience design', 2),
('Social Media Marketing', 'Marketing on social platforms', 3),
('Content Writing', 'Writing and content creation', 3),
('Project Management', 'Managing projects and teams', 4),
('Spanish Language', 'Spanish language learning', 5),
('Guitar Playing', 'Guitar instruction and learning', 6),
('Digital Photography', 'Photography skills and techniques', 7),
('Cooking', 'Culinary skills and recipes', 8),
('Fitness Training', 'Personal training and fitness', 9),
('Database Management', 'Database design and management', 10);

-- Create indexes for better performance
CREATE INDEX idx_users_username ON Users(Username);
CREATE INDEX idx_users_email ON Users(Email);
CREATE INDEX idx_userskills_userid ON UserSkills(UserID);
CREATE INDEX idx_userskills_skillid ON UserSkills(SkillID);
CREATE INDEX idx_skillrequests_userid ON SkillRequests(UserID);
CREATE INDEX idx_skillrequests_skillid ON SkillRequests(SkillID);
CREATE INDEX idx_skillrequests_status ON SkillRequests(Status);
CREATE INDEX idx_matches_requestid ON Matches(RequestID);
CREATE INDEX idx_matches_providerid ON Matches(ProviderUserID);
CREATE INDEX idx_matches_requestorid ON Matches(RequestorUserID);
CREATE INDEX idx_messages_sender ON Messages(SenderUserID);
CREATE INDEX idx_messages_receiver ON Messages(ReceiverUserID);
CREATE INDEX idx_messages_read ON Messages(IsRead);
CREATE INDEX idx_notifications_userid ON Notifications(UserID);
CREATE INDEX idx_notifications_read ON Notifications(IsRead);

-- Display success message
SELECT 'Database schema created successfully!' AS Message;
