# 🌐 Social Media Application

A modern social media platform built with Streamlit and MySQL.

## 🚀 Features

- User registration and authentication
- Create, like, and comment on posts
- Follow/unfollow users
- Real-time notifications
- Profile management
- Media sharing
- And much more!

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: MySQL
- **Authentication**: BCrypt

## 📋 Prerequisites

- Python 3.7+
- MySQL Server
- pip (Python package manager)

## ⚙️ Installation

1. Clone the repository**
   ```bash
   git clone https://github.com/yourusername/social-media-app.git
   cd social-media-app

2. Set up the database
   ```bash
   mysql -u root -p < database_schema.sql

3. Install Python dependencies
   ```bash
   pip install -r requirements.txt

4. Configure database connection
   Update the database credentials in app.py:
   ```python
   self.connection = mysql.connector.connect(
       host='localhost',
       database='social_media_db',
       user='root',
       password='your_password'
   )

5. Run the application
   ```bash
   streamlit run app.py
