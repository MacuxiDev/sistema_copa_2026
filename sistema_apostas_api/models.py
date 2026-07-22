# models.py
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
)
from sqlalchemy.orm import relationship

from database import Base


# --- Enums usados nas colunas ---
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


# --- Fase ---
class Fase(Base):
    __tablename__ = "fases"

    id_fase = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)

    grupos = relationship("Grupo", back_populates="fase")
    partidas = relationship("Partida", back_populates="fase")


# --- Grupo ---
class Grupo(Base):
    __tablename__ = "grupos"

    id_grupo = Column(Integer, primary_key=True, index=True)
    nome = Column(String(10), nullable=False)
    id_fase = Column(Integer, ForeignKey("fases.id_fase"), nullable=False)

    fase = relationship("Fase", back_populates="grupos")
    selecoes = relationship("Selecao", back_populates="grupo")


# --- Selecao ---
class Selecao(Base):
    __tablename__ = "selecoes"

    id_selecao = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    sigla = Column(String(3), nullable=False)
    id_grupo = Column(Integer, ForeignKey("grupos.id_grupo"), nullable=False)

    grupo = relationship("Grupo", back_populates="selecoes")


# --- Partida ---
class Partida(Base):
    __tablename__ = "partidas"

    id_partida = Column(Integer, primary_key=True, index=True)
    id_fase = Column(Integer, ForeignKey("fases.id_fase"), nullable=False)
    id_selecao_a = Column(Integer, ForeignKey("selecoes.id_selecao"), nullable=False)
    id_selecao_b = Column(Integer, ForeignKey("selecoes.id_selecao"), nullable=False)
    num_jogo = Column(Integer, nullable=False)
    data_hora = Column(DateTime, nullable=False)
    status = Column(Enum(StatusPartidaEnum), default=StatusPartidaEnum.agendada, nullable=False)
    gols_a = Column(Integer, nullable=True)
    gols_b = Column(Integer, nullable=True)
    odd_a = Column(Float, nullable=False)
    odd_b = Column(Float, nullable=False)
    odd_empate = Column(Float, nullable=False)

    fase = relationship("Fase", back_populates="partidas")
    selecao_a_obj = relationship("Selecao", foreign_keys=[id_selecao_a])
    selecao_b_obj = relationship("Selecao", foreign_keys=[id_selecao_b])
    apostas = relationship("Aposta", back_populates="partida")

    # Atalhos usados em crud.py (db_partida.selecao_a.nome / db_partida.selecao_b.nome)
    @property
    def selecao_a(self):
        return self.selecao_a_obj

    @property
    def selecao_b(self):
        return self.selecao_b_obj


# --- Usuario ---
class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    data_nascimento = Column(DateTime, nullable=False)
    login = Column(String(50), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    status = Column(String(20), default="ativo", nullable=False)
    tipo_usuario = Column(Enum(TipoUsuarioEnum), default=TipoUsuarioEnum.usuario, nullable=False)

    conta = relationship("Conta_Pontos", back_populates="usuario", uselist=False)
    apostas = relationship("Aposta", back_populates="usuario")


# --- Conta_Pontos ---
class Conta_Pontos(Base):
    __tablename__ = "contas_pontos"

    id_conta = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), unique=True, nullable=False)
    saldo = Column(Float, default=0.0, nullable=False)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    usuario = relationship("Usuario", back_populates="conta")
    movimentacoes = relationship("Movimentacao_Pontos", back_populates="conta")


# --- Aposta ---
class Aposta(Base):
    __tablename__ = "apostas"

    id_aposta = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_partida = Column(Integer, ForeignKey("partidas.id_partida"), nullable=False)
    palpite = Column(Enum(PalpiteEnum), nullable=False)
    pontos_apostados = Column(Float, nullable=False)
    multiplicador = Column(Integer, default=1, nullable=False)
    odd_aplicada = Column(Float, nullable=False)
    retorno_potencial = Column(Float, nullable=False)
    status = Column(Enum(StatusApostaEnum), default=StatusApostaEnum.ativa, nullable=False)
    data_hora = Column(DateTime, default=datetime.now, nullable=False)

    usuario = relationship("Usuario", back_populates="apostas")
    partida = relationship("Partida", back_populates="apostas")
    movimentacoes = relationship("Movimentacao_Pontos", back_populates="aposta")


# --- Movimentacao_Pontos ---
class Movimentacao_Pontos(Base):
    __tablename__ = "movimentacoes_pontos"

    id_movimentacao = Column(Integer, primary_key=True, index=True)
    id_conta = Column(Integer, ForeignKey("contas_pontos.id_conta"), nullable=False)
    id_aposta = Column(Integer, ForeignKey("apostas.id_aposta"), nullable=True)
    tipo_movimentacao = Column(Enum(TipoMovimentacaoEnum), nullable=False)
    pontos = Column(Float, nullable=False)
    saldo_anterior = Column(Float, nullable=False)
    saldo_atual = Column(Float, nullable=False)
    data_hora = Column(DateTime, default=datetime.now, nullable=False)
    descricao = Column(String(255), nullable=True)

    conta = relationship("Conta_Pontos", back_populates="movimentacoes")
    aposta = relationship("Aposta", back_populates="movimentacoes")