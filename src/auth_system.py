"""
Authentication system for Smart Crop Advisor
Handles user registration and login with bcrypt password hashing
"""

import sqlite3
import bcrypt
from typing import Tuple

# Initialize database connection
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


def register_user(name: str, email: str, password: str) -> Tuple[bool, str]:
    """
    Register a new user with hashed password
    
    Args:
        name: User's full name
        email: User's email address
        password: User's password (will be hashed)
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    if not name or not email or not password:
        return False, "All fields are required"
    
    try:
        # Hash password with bcrypt
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert user into database
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_pw)
        )
        conn.commit()
        return True, "Registration successful"
    
    except sqlite3.IntegrityError:
        return False, "Email already registered"
    except Exception as e:
        return False, f"Registration error: {str(e)}"


def login_user(email: str, password: str) -> bool:
    """
    Authenticate user with email and password
    
    Args:
        email: User's email address
        password: User's password (plain text)
        
    Returns:
        bool: True if authentication successful, False otherwise
    """
    if not email or not password:
        return False
    
    try:
        cursor.execute(
            "SELECT password FROM users WHERE email = ?",
            (email,)
        )
        result = cursor.fetchone()
        
        if result:
            stored_pw = result[0]
            # Verify password against stored hash
            if bcrypt.checkpw(password.encode('utf-8'), stored_pw):
                return True
        
        return False
    
    except Exception as e:
        print(f"Login error: {str(e)}")
        return False


def user_exists(email: str) -> bool:
    """
    Check if user exists by email
    
    Args:
        email: User's email address
        
    Returns:
        bool: True if user exists, False otherwise
    """
    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking user: {str(e)}")
        return False