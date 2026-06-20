import sys
import sqlite3
import os

# Add the current directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.routes.auth import hash_password
from app.db.database import DB_PATH, create_user, get_user_by_email

EMAIL = "dj@yopmail.com"
PASSWORD = "Admin@123"

def setup_admin():
    print(f"Setting up admin user: {EMAIL}")
    
    # Check if user already exists
    user = get_user_by_email(EMAIL)
    hashed_pwd = hash_password(PASSWORD)
    
    with sqlite3.connect(DB_PATH) as conn:
        if user:
            print("User already exists. Updating password and granting admin role...")
            conn.execute(
                "UPDATE users SET password_hash = ?, role = 'admin' WHERE email = ?",
                (hashed_pwd, EMAIL)
            )
            print("Successfully updated existing user.")
        else:
            print("User does not exist. Creating new user...")
            # We use create_user to ensure the subscription row is also created,
            # but then immediately override the role to 'admin' since the email doesn't contain "admin".
            create_user(EMAIL, hashed_pwd)
            conn.execute(
                "UPDATE users SET role = 'admin' WHERE email = ?",
                (EMAIL,)
            )
            print("Successfully created new admin user.")

if __name__ == "__main__":
    setup_admin()
