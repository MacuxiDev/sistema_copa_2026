# auth.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db # Importa a função para obter a sessão do DB

# --- Configurações de Segurança ---
# Para gerar uma SECRET_KEY segura, você pode usar:
# import secrets
# secrets.token_hex(32) # ou 64 para uma chave mais longa
SECRET_KEY = "sua_super_secreta_chave_jwt" # Mude para uma chave forte em produção!
ALGORITHM = "HS256" # Algoritmo de hashing para o JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Tempo de expiração do token de acesso em minutos

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de segurança OAuth2 para autenticação baseada em token
# O token será esperado no header "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Funções de Hashing e Verificação de Senhas ---
def get_password_hash(password: str) -> str:
    """
    Gera o hash de uma senha.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

# --- Funções de Geração e Validação de JWT ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token de acesso JWT.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Usuario:
    """
    Dependência para obter o usuário atual a partir do token JWT.
    Verifica a validade do token e busca o usuário no banco de dados
    """

