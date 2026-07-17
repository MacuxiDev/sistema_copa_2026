# schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
import enum

# --- Enums (copiados de models.py, se necessário, ou redefinidos para Pydantic) ---
# Se você já tem enums no models.py, pode importá-los ou redefini-los aqui.
# Para simplicidade e para evitar dependência circular inicial, vamos redefini-los.

class StatusPartidaEnum(str, enum.Enum):
    agendada = "agendada"
    em_andamento = "em_andamento"
    finalizada = "finalizada"
    cancelada = "cancelada"

class PalpiteEnum(str, enum.Enum):
    selecao_a = "selecao_a"
    selecao_b = "selecao_b"
    empate = "empate"

class StatusApostaEnum(str, enum.Enum):
    ativa = "ativa"
    ganha = "ganha"
    perdida = "perdida"
    reembolsada = "reembolsada"

class TipoMovimentacaoEnum(str, enum.Enum):
    credito = "credito"
    debito = "debito"
    estorno = "estorno"

class TipoUsuarioEnum(str, enum.Enum):
    usuario = "usuario"
    admin = "admin"

# --- Schemas para Entidades (Base, Create, Update, Response) ---

# Movimentacao_Pontos
class MovimentacaoPontosBase(BaseModel):
    tipo_movimentacao: TipoMovimentacaoEnum
    pontos: float
    saldo_anterior: float
    saldo_atual: float
    descricao: str

class MovimentacaoPontosCreate(MovimentacaoPontosBase):
    pass

class MovimentacaoPontos(MovimentacaoPontosBase):
    id_movimentacao: int
    id_conta: int
    id_aposta: Optional[int] = None
    data_hora: datetime

    class Config:
        from_attributes = True # Permite que o Pydantic leia dados de um ORM (SQLAlchemy)

# Conta_Pontos
class ContaPontosBase(BaseModel):
    saldo: float

class ContaPontosCreate(ContaPontosBase):
    pass

class ContaPontos(ContaPontosBase):
    id_conta: int
    id_usuario: int
    data_atualizacao: datetime
    movimentacoes: List[MovimentacaoPontos] = [] # Inclui movimentações aninhadas

    class Config:
        from_attributes = True

# Usuario
class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    cpf: str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
    data_nascimento: datetime
    login: str = Field(..., min_length=3, max_length=50)
    status: str = "ativo" # Default para novo usuário
    tipo_usuario: TipoUsuarioEnum = TipoUsuarioEnum.usuario # Default

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=8) # Senha é necessária na criação

class UsuarioUpdate(UsuarioBase):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    data_nascimento: Optional[datetime] = None
    login: Optional[str] = None
    status: Optional[str] = None
    tipo_usuario: Optional[TipoUsuarioEnum] = None
    senha: Optional[str] = None # Permite atualizar a senha

class Usuario(UsuarioBase):
    id_usuario: int
    senha_hash: str # Não expomos a senha, mas sim o hash (apenas para debug/admin, idealmente não seria exposto)
    conta: Optional[ContaPontos] = None # Inclui a conta de pontos aninhada
    apostas: List["Aposta"] = [] # Forward reference para Aposta

    class Config:
        from_attributes = True

# Fase
class FaseBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=50)
    data_inicio: datetime
    data_fim: datetime

class FaseCreate(FaseBase):
    pass

class Fase(FaseBase):
    id_fase: int
    # grupos: List["Grupo"] = [] # Evitar dependência circular aqui por enquanto

    class Config:
        from_attributes = True

# Grupo
class GrupoBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=10) # Ex: "A", "B", "C"

class GrupoCreate(GrupoBase):
    id_fase: int

class Grupo(GrupoBase):
    id_grupo: int
    id_fase: int
    # selecoes: List["Selecao"] = [] # Evitar dependência circular aqui por enquanto

    class Config:
        from_attributes = True

# Selecao
class SelecaoBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=50)
    sigla: str = Field(..., min_length=2, max_length=3)

class SelecaoCreate(SelecaoBase):
    id_grupo: int

class Selecao(SelecaoBase):
    id_selecao: int
    id_grupo: int

    class Config:
        from_attributes = True

# Partida
class PartidaBase(BaseModel):
    id_fase: int
    id_selecao_a: int
    id_selecao_b: int
    num_jogo: int
    data_hora: datetime
    status: StatusPartidaEnum = StatusPartidaEnum.agendada
    gols_a: Optional[int] = None
    gols_b: Optional[int] = None
    odd_a: float = Field(..., gt=0)
    odd_b: float = Field(..., gt=0)
    odd_empate: float = Field(..., gt=0)

class PartidaCreate(PartidaBase):
    pass

class PartidaUpdate(BaseModel):
    status: Optional[StatusPartidaEnum] = None
    gols_a: Optional[int] = None
    gols_b: Optional[int] = None
    odd_a: Optional[float] = None
    odd_b: Optional[float] = None
    odd_empate: Optional[float] = None

class Partida(PartidaBase):
    id_partida: int
    selecao_a_obj: Optional[Selecao] = None # Objeto Selecao aninhado
    selecao_b_obj: Optional[Selecao] = None # Objeto Selecao aninhado

    class Config:
        from_attributes = True

# Aposta
class ApostaBase(BaseModel):
    id_partida: int
    palpite: PalpiteEnum
    pontos_apostados: float = Field(..., gt=0)
    multiplicador: int = Field(1, ge=1) # Multiplicador padrão 1, mínimo 1

class ApostaCreate(ApostaBase):
    pass

class Aposta(ApostaBase):
    id_aposta: int
    id_usuario: int
    odd_aplicada: float
    retorno_potencial: float
    status: StatusApostaEnum
    data_hora: datetime
    partida: Optional[Partida] = None # Inclui a partida aninhada

    class Config:
        from_attributes = True

# --- Schemas para Autenticação ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Schemas para Ranking ---
class RankingEntry(BaseModel):
    posicao: int
    login: str
    saldo: float
    apostas_ganhas: int
    apostas_perdidas: int
    apostas_ativas: int
    apostas_reembolsadas: int
    total_apostas: int
    taxa_acerto_pct: float

    class Config:
        from_attributes = True

# --- Forward References para resolver dependências circulares ---
# Isso é necessário para que Pydantic possa resolver tipos que se referenciam mutuamente.
Usuario.model_rebuild()
Aposta.model_rebuild()