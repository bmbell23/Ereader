#!/usr/bin/env python3
"""Script to create the brandon user for GreatReads."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from greatreads.database import get_db_session, create_tables
from greatreads.models.user import User
from greatreads.auth import get_password_hash


def main():
    """Create brandon user."""
    print("=" * 60)
    print("  Creating Brandon User for GreatReads")
    print("=" * 60)
    print()

    # Ensure tables exist
    create_tables()

    password = input("Enter password for 'brandon': ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        return

    with get_db_session() as db:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == "brandon").first()
        if existing_user:
            print("❌ User 'brandon' already exists!")
            print()
            update = input("Do you want to update the password? (y/n): ").strip().lower()
            if update == 'y':
                existing_user.password_hash = get_password_hash(password)
                db.commit()
                print("✅ Password updated successfully!")
            return

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            username="brandon",
            email="bbell.primary@gmail.com",
            password_hash=hashed_password,
            display_name="Brandon",
            is_active=True,
            is_admin=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print("✅ User 'brandon' created successfully!")
        print(f"   Email: {new_user.email}")
        print(f"   Display Name: {new_user.display_name}")
        print()


if __name__ == "__main__":
    main()

