# main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from database import create_db_and_tables, get_db
import crud
from routers import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando a aplicação...")
    create_db_and_tables()
    print("Tabelas do banco de dados verificadas/criadas.")

    with next(get_db()) as db:
        crud.seed_data(db)
    print("Processo de seed de dados concluído.")

    yield
    # Código de encerramento (shutdown) pode ser adicionado aqui, se necessário


app = FastAPI(
    title="API de Apostas Copa 2026",
    description="API para gerenciar usuários, contas, partidas, apostas e ranking para a Copa do Mundo de 2026.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(users.router)


@app.get("/", tags=["Root"])
async def read_root():
    """
    Endpoint de saúde da API.
    Retorna uma mensagem de boas-vindas.
    """
    return {"message": "Bem-vindo à API de Apostas da Copa 2026!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)