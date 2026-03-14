from datetime import datetime, timezone, timedelta

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash

from src.config import settings


class AuthService:
    password_hash = PasswordHash.recommended()

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def get_password_hash(self, password):
        return self.password_hash.hash(password)

    def verify_password(self, plain_password, password_hash):
        return self.password_hash.verify(plain_password, password_hash)

    def decode_token(self, token):
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Токен истек")
        except jwt.InvalidSignatureError:
            raise HTTPException(status_code=401, detail="Неверная подпись токена")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Неверный JWT токен")
