# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import uvicorn

from .database import create_db_and_tables, get_db
from . import crud
# from .routers import users, matches, bets # Manter comentado por enquanto

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="API de Apostas Copa 2026",
    description="API para gerenciar usuários, contas, partidas, apostas e ranking para a Copa do Mundo de 2026.",
    version="0.1.0",
)

# Evento de inicialização da aplicação
@app.on_event("startup")
def on_startup():
    print("Iniciando a aplicação...")
    create_db_and_tables() # Cria as tabelas no banco de dados
    print("Tabelas do banco de dados verificadas/criadas.")

    # Popula o banco de dados com dados iniciais (seed)
    # Usamos um gerador de sessão temporário para a função seed_data
    with next(get_db()) as db:
        crud.seed_data(db)
    print("Processo de seed de dados concluído.")


@app.get("/", tags=["Root"])
async def read_root():
    """
    Endpoint de saúde da API.
    Retorna uma mensagem de boas-vindas.
    """
    return {"message": "Bem-vindo à API de Apostas da Copa 2026!"}

# O bloco if __name__ == "__main__":
# Este bloco será executado APENAS quando o arquivo main.py for executado diretamente.
# Ele não será executado se main.py for importado como um módulo.
if __name__ == "__main__":
    # Inicia o servidor Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)