# routers/users.py
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud, schemas, auth
from database import get_db

# Cria um APIRouter para agrupar os endpoints de usuário
router = APIRouter(
    prefix="/users",  # Prefixo para todas as rotas neste router (ex: /users/me)
    tags=["Users"],   # Tag para agrupar na documentação interativa (Swagger UI)
)

# Endpoint para criar um novo usuário
@router.post("/", response_model=schemas.Usuario)
def create_user(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_user = crud.get_usuario_by_login(db, login=user.login)
    if db_user:
        raise HTTPException(status_code=400, detail="Login já registrado")
    db_user = crud.get_usuario_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    db_user = crud.get_usuario_by_cpf(db, cpf=user.cpf)
    if db_user:
        raise HTTPException(status_code=400, detail="CPF já registrado")

    new_user = crud.create_usuario(db=db, user=user)
    if isinstance(new_user, dict) and "erro" in new_user:  # Tratamento de erro do CPF inválido
        raise HTTPException(status_code=400, detail=new_user["erro"])
    return new_user

# Endpoint para login (obter token de acesso)
@router.post("/token", response_model=schemas.Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_usuario_by_login(db, login=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint para obter informações do usuário logado
@router.get("/me", response_model=schemas.Usuario)
async def read_users_me(current_user: schemas.Usuario = Depends(auth.get_current_active_user)):
    return current_user

# Endpoint para listar todos os usuários (apenas para administradores)
@router.get("/", response_model=List[schemas.Usuario])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                      current_admin: schemas.Usuario = Depends(auth.get_current_admin_user)):
    users = crud.get_usuarios(db, skip=skip, limit=limit)
    return users