from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base, SessionLocal
from services.auth_service import auth_service
from schemas.auth import UserCreate

# Routers
from routers import dashboard, query, balance, data_mgmt, agent, auth, optimizer

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="产销平衡系统 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize admin user
try:
    db = SessionLocal()
    if not auth_service.get_user_by_username(db, "admin"):
        admin_user = UserCreate(username="admin", password="admin-password", roles=["admin"])
        auth_service.create_user(db, admin_user)
        print("Initialized default admin user: admin/admin-password")
    db.close()
except Exception as e:
    print(f"Error initializing database: {e}")

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(dashboard.router, prefix="/api/cockpit", tags=["驾驶舱"])
app.include_router(query.router, prefix="/api/query", tags=["查询"])
app.include_router(balance.router, prefix="/api/balance", tags=["产销平衡"])
app.include_router(data_mgmt.router, prefix="/api/data", tags=["数据管理"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI问数"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["运筹优化引擎"])

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
