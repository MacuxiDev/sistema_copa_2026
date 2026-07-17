# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool # Importar StaticPool para SQLite

# URL do banco de dados SQLite. O arquivo 'apostas_copa2026.db' será criado na raiz do projeto.
SQLALCHEMY_DATABASE_URL = "sqlite:///./apostas_copa2026.db"

# Configuração do Engine para SQLite
# connect_args é necessário para que o SQLite funcione corretamente com múltiplos threads no FastAPI
# poolclass=StaticPool é usado para garantir que a mesma conexão seja usada para cada requisição
# no ambiente de desenvolvimento com SQLite, evitando problemas de "thread safety".
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool # Adicionado para SQLite em ambiente de desenvolvimento
)

# Cria uma SessionLocal, que será a classe de sessão do banco de dados.
# autocommit=False garante que as transações não sejam commitadas automaticamente.
# autoflush=False desabilita o autoflush para maior controle.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para os modelos SQLAlchemy
Base = declarative_base()

# Função para obter uma sessão de banco de dados
# Esta função será usada como uma dependência no FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para criar todas as tabelas no banco de dados
def create_db_tables():
    Base.metadata.create_all(bind=engine)
    print("Tabelas do banco de dados criadas (ou já existentes).")

# Importar os modelos para que o Base.metadata.create_all os reconheça
# Isso deve ser feito DEPOIS de Base ser definido
from . import models