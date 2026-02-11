import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRY_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

pwdContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashPassword(password: str):
    """Hash password using bcrypt."""
    return pwdContext.hash(password)


def verifyPassword(plainPassword: str, hashedPassword: str):
    """Verify plaintext password against hash."""
    return pwdContext.verify(plainPassword, hashedPassword)


def createAccessToken(data: dict):
    """Generate JWT token with expiration."""
    toEncode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRY_MINUTES)
    toEncode.update({"exp": expire})
    return jwt.encode(toEncode, SECRET_KEY, algorithm=ALGORITHM)


