from core.database import SessionLocal
from services.auth_service import auth_service
from schemas.auth import UserCreate
from core.security import get_password_hash

db = SessionLocal()
try:
    user = auth_service.get_user_by_username(db, "admin")
    if user:
        print("Admin user found. Resetting password...")
        user.hashed_password = get_password_hash("admin-password")
        db.commit()
        print("Password reset to 'admin-password'")
    else:
        print("Admin user not found. Creating...")
        admin_user = UserCreate(username="admin", password="admin-password", roles=["admin"])
        auth_service.create_user(db, admin_user)
        print("Admin user created with 'admin-password'")
finally:
    db.close()
