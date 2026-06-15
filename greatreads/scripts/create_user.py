#!/usr/bin/env python3
"""Script to create a user for GreatReads."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from greatreads.database import get_db_session
from greatreads.models.user import User
from greatreads.auth import get_password_hash


def create_user(username: str, email: str, password: str, display_name: str = None):
    """Create a new user."""
    with get_db_session() as db:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return False

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            display_name=display_name or username,
            is_active=True,
            is_admin=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✅ User '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Display Name: {new_user.display_name}")
        return True


def main():
    """Main function."""
    print("=" * 60)
    print("  GreatReads User Creation")
    print("=" * 60)
    print()

    # Get user input
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return

    email = input("Email: ").strip()
    if not email:
        print("❌ Email cannot be empty!")
        return

    password = input("Password: ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        return

    display_name = input("Display Name (optional, press Enter to use username): ").strip()

    print()
    create_user(username, email, password, display_name or None)
    print()


if __name__ == "__main__":
    main()

