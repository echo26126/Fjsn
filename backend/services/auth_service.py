from sqlalchemy.orm import Session
from models.user import User
from schemas.auth import UserCreate, UserUpdate
from core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def get_user_by_username(self, db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    def create_user(self, db: Session, user: UserCreate):
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            hashed_password=hashed_password,
            roles=user.roles
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(self, db: Session, username: str, password: str):
        user = self.get_user_by_username(db, username)
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user

    def create_token_for_user(self, user: User):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "roles": user.roles},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    def update_user(self, db: Session, user_id: int, user_update: UserUpdate):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        if user_update.roles is not None:
            user.roles = user_update.roles
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        if user_update.password:
            user.hashed_password = get_password_hash(user_update.password)
            
        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    
    def list_users(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(User).offset(skip).limit(limit).all()

auth_service = AuthService()
