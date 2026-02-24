from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional
from .env import MONGO_URI, DB_NAME

app = FastAPI()

# 1. SETUP ASYNC DB CONNECTION (MOTOR)
# Motor is non-blocking. It allows the server to handle other requests while waiting for DB.
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME] 
sessions_collection = db["sessions"]

# 2. DEFINE SECURITY SCHEME
# This tells Swagger UI to expect an "Authorization" header.
header_scheme = APIKeyHeader(name="Authorization", auto_error=False)

# 3. THE AUTH DEPENDENCY (Replaces Middleware)
async def get_current_user(token: str = Depends(header_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="No token provided"
        )

    # Clean the token if it has "Bearer " prefix
    cleaned_token = token.replace("Bearer ", "") if token.startswith("Bearer ") else token

    # 4. ASYNC DB QUERY
    # We use 'await' here so the server doesn't freeze.
    session = await sessions_collection.find_one({"token": cleaned_token})

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid session"
        )

    # 5. TIMEZONE AWARE CHECK
    # datetime.utcnow() is deprecated. Use timezone-aware UTC.
    if session["expiresAt"] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session expired"
        )

    return session["userId"]