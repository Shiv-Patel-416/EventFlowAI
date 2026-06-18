"""Authentication Router"""
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.utils.auth import hash_password, verify_password, create_access_token
import uuid

router = APIRouter()

# In-memory user store (for prototype — in production, use PostgreSQL)
USERS_DB = {
    "admin": {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "email": "admin@eventflow.ai",
        "password_hash": hash_password("admin123"),
        "full_name": "System Administrator",
        "role": "admin",
        "police_station": "Central HQ",
        "zone": "All Zones",
        "is_active": True
    },
    "officer1": {
        "id": str(uuid.uuid4()),
        "username": "officer1",
        "email": "officer@eventflow.ai",
        "password_hash": hash_password("officer123"),
        "full_name": "Traffic Officer",
        "role": "officer",
        "police_station": "Cubbon Park",
        "zone": "Central Zone 2",
        "is_active": True
    }
}

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = USERS_DB.get(data.username)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"], "username": user["username"], "role": user["role"]})
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            police_station=user["police_station"],
            zone=user["zone"],
            is_active=user["is_active"]
        )
    )

@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate):
    if data.username in USERS_DB:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = str(uuid.uuid4())
    USERS_DB[data.username] = {
        "id": user_id,
        "username": data.username,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "role": data.role,
        "police_station": data.police_station,
        "zone": data.zone,
        "is_active": True
    }
    
    return UserResponse(
        id=user_id,
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        police_station=data.police_station,
        zone=data.zone,
        is_active=True
    )
