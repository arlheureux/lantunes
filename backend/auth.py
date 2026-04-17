import jwt
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def get_secret_key():
    """Get JWT secret key from env var or generate secure random one."""
    env_secret = os.environ.get("JWT_SECRET")
    if env_secret:
        return env_secret
    
    secret_file = Path(__file__).parent / ".jwt_secret"
    
    if secret_file.exists():
        return secret_file.read_text().strip()
    
    new_secret = secrets.token_hex(32)
    secret_file.write_text(new_secret)
    os.chmod(secret_file, 0o600)
    
    return new_secret

SECRET_KEY = get_secret_key()

def create_access_token(data: dict) -> str:
    """Create JWT access token with 24h expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    import bcrypt
    
    if password_hash.startswith('$2'):
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception:
            return False
    return False