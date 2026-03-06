from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from services.auth_service import AuthService
from schemas.auth import UserRead, UserCreate, Token, UserUpdate, UserLogin
from datetime import timedelta
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

auth_service = AuthService()

# Token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login_json(payload: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import JWTError, jwt
    from core.security import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = auth_service.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/users", response_model=list[UserRead])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UserRead = Depends(read_users_me)):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return auth_service.list_users(db, skip=skip, limit=limit)

@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: UserRead = Depends(read_users_me)):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    db_user = auth_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return auth_service.create_user(db=db, user=user)

@router.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: UserRead = Depends(read_users_me)):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    updated_user = auth_service.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: UserRead = Depends(read_users_me)):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    success = auth_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}
