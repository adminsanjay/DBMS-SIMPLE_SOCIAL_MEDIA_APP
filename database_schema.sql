-- Social Media App Database Schema
CREATE DATABASE IF NOT EXISTS social_media_db;
USE social_media_db;

-- Users Table
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Gender ENUM('M', 'F', 'O'),
    DOB DATE,
    Bio TEXT,
    IsPrivate ENUM('Y', 'N') DEFAULT 'N',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UserProfile Table
CREATE TABLE UserProfile (
    ProfileID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    AvatarURL VARCHAR(255),
    Website VARCHAR(255),
    Location VARCHAR(100),
    About TEXT,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Posts Table
CREATE TABLE Posts (
    PostID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Content TEXT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Media Table
CREATE TABLE Media (
    MediaID INT AUTO_INCREMENT PRIMARY KEY,
    PostID INT NOT NULL,
    MediaURL VARCHAR(255) NOT NULL,
    MediaType ENUM('image', 'video') NOT NULL,
    FOREIGN KEY (PostID) REFERENCES Posts(PostID) ON DELETE CASCADE
);

-- Followers Table
CREATE TABLE Followers (
    FollowerID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,  -- The user being followed
    FollowerUserID INT NOT NULL,  -- The user who is following
    Status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
    RequestedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    RespondedAt TIMESTAMP NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (FollowerUserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    UNIQUE KEY unique_follow (UserID, FollowerUserID)
);

-- Likes Table
CREATE TABLE Likes (
    LikeID INT AUTO_INCREMENT PRIMARY KEY,
    PostID INT NOT NULL,
    UserID INT NOT NULL,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PostID) REFERENCES Posts(PostID) ON DELETE CASCADE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    UNIQUE KEY unique_like (PostID, UserID)
);

-- Comments Table
CREATE TABLE Comments (
    CommentID INT AUTO_INCREMENT PRIMARY KEY,
    PostID INT NOT NULL,
    UserID INT NOT NULL,
    TextComment TEXT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PostID) REFERENCES Posts(PostID) ON DELETE CASCADE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Shares Table
CREATE TABLE Shares (
    ShareID INT AUTO_INCREMENT PRIMARY KEY,
    PostID INT NOT NULL,
    UserID INT NOT NULL,
    Message TEXT,
    SharedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PostID) REFERENCES Posts(PostID) ON DELETE CASCADE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Notifications Table
CREATE TABLE Notifications (
    NotificationID INT AUTO_INCREMENT PRIMARY KEY,
    SenderID INT NOT NULL,
    ReceiverID INT NOT NULL,
    Message TEXT NOT NULL,
    Type ENUM('like', 'comment', 'follow_request', 'follow_accept', 'follow_reject', 'share'),
    IsRead ENUM('Y', 'N') DEFAULT 'N',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SenderID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ReceiverID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX idx_posts_user ON Posts(UserID);
CREATE INDEX idx_posts_created ON Posts(CreatedAt);
CREATE INDEX idx_followers_user ON Followers(UserID);
CREATE INDEX idx_followers_follower ON Followers(FollowerUserID);
CREATE INDEX idx_likes_post ON Likes(PostID);
CREATE INDEX idx_comments_post ON Comments(PostID);
CREATE INDEX idx_notifications_receiver ON Notifications(ReceiverID);
