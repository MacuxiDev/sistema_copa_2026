# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from datetime import datetime, timedelta

import models, schemas
from auth import get_password_hash
from validation import validar_cpf

# --- Funções CRUD para Usuário ---
def get_usuario_by_login(db: Session, login: str):
    return db.query(models.Usuario).filter(models.Usuario.login == login).first()

def get_usuario_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def get_usuario_by_cpf(db: Session, cpf: str):
    return db.query(models.Usuario).filter(models.Usuario.cpf == cpf).first()

def create_usuario(db: Session, user: schemas.UsuarioCreate):
    # Validação de CPF
    if not validar_cpf(user.cpf):
        return {"erro": "CPF inválido."}

    # Verificar se login, email ou CPF já existem
    if get_usuario_by_login(db, user.login):
        return {"erro": "Login já cadastrado."}
    if get_usuario_by_email(db, user.email):
        return {"erro": "Email já cadastrado."}
    if get_usuario_by_cpf(db, user.cpf):
        return {"erro": "CPF já cadastrado."}

    hashed_password = get_password_hash(user.senha)
    db_user = models.Usuario(
        nome=user.nome,
        email=user.email,
        cpf=user.cpf,
        data_nascimento=user.data_nascimento,
        login=user.login,
        senha_hash=hashed_password,
        status="ativo",
        tipo_usuario=user.tipo_usuario
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Criar conta de pontos para o novo usuário
    db_conta = models.Conta_Pontos(id_usuario=db_user.id_usuario, saldo=100.0)
    db.add(db_conta)
    db.commit()
    db.refresh(db_conta)

    # Registrar movimentação de bônus de boas-vindas
    db_mov = models.Movimentacao_Pontos(
        id_conta=db_conta.id_conta,
        tipo_movimentacao=schemas.TipoMovimentacaoEnum.credito,
        pontos=100.0,
        saldo_anterior=0.0,
        saldo_atual=100.0,
        data_hora=datetime.now(),
        descricao="Bônus de boas-vindas"
    )
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)

    return db_user

def get_usuario(db: Session, id_usuario: int):
    return db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

# --- Funções CRUD para Partida ---
def get_partida(db: Session, id_partida: int):
    return db.query(models.Partida).filter(models.Partida.id_partida == id_partida).first()

def get_partidas_agendadas(db: Session, id_usuario: int, skip: int = 0, limit: int = 5):
    # Retorna partidas agendadas que o usuário ainda não apostou
    subquery = db.query(models.Aposta.id_partida).filter(models.Aposta.id_usuario == id_usuario).subquery()
    return db.query(models.Partida).filter(
        models.Partida.status == schemas.StatusPartidaEnum.agendada,
        ~models.Partida.id_partida.in_(subquery)
    ).order_by(models.Partida.num_jogo.asc()).offset(skip).limit(limit).all()

def update_partida_status(db: Session, id_partida: int, status: schemas.StatusPartidaEnum):
    db_partida = get_partida(db, id_partida)
    if db_partida:
        db_partida.status = status
        db.commit()
        db.refresh(db_partida)
    return db_partida

def liquidar_partida(db: Session, id_partida: int, gols_a: int, gols_b: int):
    db_partida = get_partida(db, id_partida)
    if not db_partida or db_partida.status != schemas.StatusPartidaEnum.em_andamento:
        return {"erro": "Partida não encontrada ou não está em andamento para liquidação."}

    db_partida.gols_a = gols_a
    db_partida.gols_b = gols_b
    db_partida.status = schemas.StatusPartidaEnum.finalizada
    db.commit()
    db.refresh(db_partida)

    # Determinar o resultado da partida
    if gols_a > gols_b:
        resultado_partida = schemas.PalpiteEnum.selecao_a
    elif gols_b > gols_a:
        resultado_partida = schemas.PalpiteEnum.selecao_b
    else:
        resultado_partida = schemas.PalpiteEnum.empate

    # Liquidar apostas
    apostas_da_partida = db.query(models.Aposta).filter(
        models.Aposta.id_partida == id_partida,
        models.Aposta.status == schemas.StatusApostaEnum.ativa
    ).all()

    for aposta in apostas_da_partida:
        db_conta = db.query(models.Conta_Pontos).filter(models.Conta_Pontos.id_usuario == aposta.id_usuario).first()
        if not db_conta:
            print(f"Erro: Conta de pontos não encontrada para o usuário {aposta.id_usuario}")
            continue

        saldo_anterior = db_conta.saldo
        if aposta.palpite == resultado_partida:
            # Aposta ganha
            retorno = aposta.retorno_potencial
            db_conta.saldo += retorno
            aposta.status = schemas.StatusApostaEnum.ganha
            descricao = f"Aposta GANHA na partida {db_partida.id_partida} (Palpite: {aposta.palpite.value})"
            tipo_mov = schemas.TipoMovimentacaoEnum.credito
        else:
            # Aposta perdida
            aposta.status = schemas.StatusApostaEnum.perdida
            retorno = 0.0 # Não há retorno para aposta perdida
            descricao = f"Aposta PERDIDA na partida {db_partida.id_partida} (Palpite: {aposta.palpite.value})"
            tipo_mov = schemas.TipoMovimentacaoEnum.debito # O débito já ocorreu na criação, isso é apenas para registro

        db_conta.data_atualizacao = datetime.now()
        db.add(db_conta)
        db.add(aposta)
        db.commit()
        db.refresh(db_conta)
        db.refresh(aposta)

        # Registrar movimentação
        db_mov = models.Movimentacao_Pontos(
            id_conta=db_conta.id_conta,
            id_aposta=aposta.id_aposta,
            tipo_movimentacao=tipo_mov,
            pontos=retorno if tipo_mov == schemas.TipoMovimentacaoEnum.credito else 0.0, # Pontos creditados
            saldo_anterior=saldo_anterior,
            saldo_atual=db_conta.saldo,
            data_hora=datetime.now(),
            descricao=descricao
        )
        db.add(db_mov)
        db.commit()
        db.refresh(db_mov)

    return db_partida

def cancelar_partida(db: Session, id_partida: int, motivo: str):
    db_partida = get_partida(db, id_partida)
    if not db_partida or db_partida.status != schemas.StatusPartidaEnum.agendada:
        return {"erro": "Partida não encontrada ou não está agendada para cancelamento."}

    db_partida.status = schemas.StatusPartidaEnum.cancelada
    db.commit()
    db.refresh(db_partida)

    # Reembolsar apostas ativas
    apostas_da_partida = db.query(models.Aposta).filter(
        models.Aposta.id_partida == id_partida,
        models.Aposta.status == schemas.StatusApostaEnum.ativa
    ).all()

    for aposta in apostas_da_partida:
        db_conta = db.query(models.Conta_Pontos).filter(models.Conta_Pontos.id_usuario == aposta.id_usuario).first()
        if not db_conta:
            print(f"Erro: Conta de pontos não encontrada para o usuário {aposta.id_usuario}")
            continue

        saldo_anterior = db_conta.saldo
        reembolso = aposta.pontos_apostados * aposta.multiplicador # Reembolsa o valor apostado * multiplicador
        db_conta.saldo += reembolso
        db_conta.data_atualizacao = datetime.now()
        aposta.status = schemas.StatusApostaEnum.reembolsada
        descricao = f"Reembolso — Jogo {db_partida.num_jogo}: {db_partida.selecao_a.nome} x {db_partida.selecao_b.nome} cancelado | {motivo}"

        db.add(db_conta)
        db.add(aposta)
        db.commit()
        db.refresh(db_conta)
        db.refresh(aposta)

        # Registrar movimentação de reembolso
        db_mov = models.Movimentacao_Pontos(
            id_conta=db_conta.id_conta,
            id_aposta=aposta.id_aposta,
            tipo_movimentacao=schemas.TipoMovimentacaoEnum.estorno,
            pontos=reembolso,
            saldo_anterior=saldo_anterior,
            saldo_atual=db_conta.saldo,
            data_hora=datetime.now(),
            descricao=descricao
        )
        db.add(db_mov)
        db.commit()
        db.refresh(db_mov)

    return db_partida

# --- Funções CRUD para Aposta ---
def get_aposta(db: Session, id_aposta: int):
    return db.query(models.Aposta).filter(models.Aposta.id_aposta == id_aposta).first()

def get_apostas_usuario(db: Session, id_usuario: int, skip: int = 0, limit: int = 100):
    return db.query(models.Aposta).filter(models.Aposta.id_usuario == id_usuario).offset(skip).limit(limit).all()

def create_aposta(db: Session, aposta: schemas.ApostaCreate, id_usuario: int):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not db_usuario:
        return {"erro": "Usuário não encontrado."}

    db_conta = db.query(models.Conta_Pontos).filter(models.Conta_Pontos.id_usuario == id_usuario).first()
    if not db_conta:
        return {"erro": "Conta de pontos não encontrada para o usuário."}

    db_partida = db.query(models.Partida).filter(models.Partida.id_partida == aposta.id_partida).first()
    if not db_partida:
        return {"erro": "Partida não encontrada."}

    if db_partida.status != schemas.StatusPartidaEnum.agendada:
        return {"erro": "Não é possível apostar em partidas que não estão agendadas."}

    # Verificar se o usuário já apostou nesta partida
    aposta_existente = db.query(models.Aposta).filter(
        models.Aposta.id_usuario == id_usuario,
        models.Aposta.id_partida == aposta.id_partida
    ).first()
    if aposta_existente:
        return {"erro": "Você já apostou nesta partida."}

    # Verificar saldo
    valor_total_aposta = aposta.pontos_apostados * aposta.multiplicador
    if db_conta.saldo < valor_total_aposta:
        return {"erro": "Saldo insuficiente para realizar esta aposta."}

    # Obter a odd aplicada
    if aposta.palpite == schemas.PalpiteEnum.selecao_a:
        odd_aplicada = db_partida.odd_a
    elif aposta.palpite == schemas.PalpiteEnum.selecao_b:
        odd_aplicada = db_partida.odd_b
    elif aposta.palpite == schemas.PalpiteEnum.empate:
        odd_aplicada = db_partida.odd_empate
    else:
        return {"erro": "Palpite inválido."}

    if odd_aplicada is None or odd_aplicada <= 0:
        return {"erro": "Odd inválida para o palpite selecionado."}

    retorno_potencial = valor_total_aposta * odd_aplicada

    # Debitar saldo
    saldo_anterior = db_conta.saldo
    db_conta.saldo -= valor_total_aposta
    db_conta.data_atualizacao = datetime.now()

    db_aposta = models.Aposta(
        id_usuario=id_usuario,
        id_partida=aposta.id_partida,
        palpite=aposta.palpite,
        pontos_apostados=aposta.pontos_apostados,
        multiplicador=aposta.multiplicador,
        odd_aplicada=odd_aplicada,
        retorno_potencial=retorno_potencial,
        status=schemas.StatusApostaEnum.ativa,
        data_hora=datetime.now()
    )

    db.add(db_conta)
    db.add(db_aposta)
    db.commit()
    db.refresh(db_conta)
    db.refresh(db_aposta)

    # Registrar movimentação
    db_mov = models.Movimentacao_Pontos(
        id_conta=db_conta.id_conta,
        id_aposta=db_aposta.id_aposta,
        tipo_movimentacao=schemas.TipoMovimentacaoEnum.debito,
        pontos=valor_total_aposta,
        saldo_anterior=saldo_anterior,
        saldo_atual=db_conta.saldo,
        data_hora=datetime.now(),
        descricao=f"Aposta em {db_partida.selecao_a.nome} x {db_partida.selecao_b.nome} (Palpite: {aposta.palpite.value})"
    )
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)

    return db_aposta

# --- Funções para Ranking ---
def get_ranking(db: Session, limit: int = 10):
    # Esta função assume que a VIEW 'ranking_geral' já foi criada no banco de dados.
    # A VIEW deve calcular os saldos e estatísticas de apostas.
    # No seu `main.py`, a função `create_db_and_tables` já cria a VIEW.
    ranking_data = db.execute(
        "SELECT * FROM ranking_geral ORDER BY saldo DESC LIMIT :limit",
        {"limit": limit}
    ).fetchall()

    ranking_list = []
    for i, row in enumerate(ranking_data):
        ranking_list.append(schemas.RankingEntry(
            posicao=i + 1,
            login=row.login,
            saldo=row.saldo,
            apostas_ganhas=row.apostas_ganhas,
            apostas_perdidas=row.apostas_perdidas,
            apostas_ativas=row.apostas_ativas,
            apostas_reembolsadas=row.apostas_reembolsadas,
            total_apostas=row.total_apostas,
            taxa_acerto_pct=row.taxa_acerto_pct
        ))
    return ranking_list

# --- Funções para Popular o Banco de Dados (Seed) ---
def seed_data(db: Session):
    # Verificar se já existem dados para evitar duplicação
    if db.query(models.Fase).first():
        print("Dados de seed já existem no banco de dados. Pulando seed.")
        return

    print("Populando o banco de dados com dados iniciais (seed)...")

    # Fases
    hoje = datetime.now()
    fase_grupos = models.Fase(nome="Fase de Grupos", data_inicio=hoje, data_fim=hoje + timedelta(days=15))
    fase_oitavas = models.Fase(nome="Oitavas de Final", data_inicio=hoje + timedelta(days=16), data_fim=hoje + timedelta(days=19))
    fase_quartas = models.Fase(nome="Quartas de Final", data_inicio=hoje + timedelta(days=20), data_fim=hoje + timedelta(days=22))
    fase_semifinal = models.Fase(nome="Semifinal", data_inicio=hoje + timedelta(days=23), data_fim=hoje + timedelta(days=24))
    fase_final = models.Fase(nome="Final", data_inicio=hoje + timedelta(days=25), data_fim=hoje + timedelta(days=25))
    db.add_all([fase_grupos, fase_oitavas, fase_quartas, fase_semifinal, fase_final])
    db.commit()
    db.refresh(fase_grupos)
    db.refresh(fase_oitavas)
    db.refresh(fase_quartas)
    db.refresh(fase_semifinal)
    db.refresh(fase_final)

    # Grupos
    grupo_a = models.Grupo(nome="Grupo A", id_fase=fase_grupos.id_fase)
    grupo_b = models.Grupo(nome="Grupo B", id_fase=fase_grupos.id_fase)
    db.add_all([grupo_a, grupo_b])
    db.commit()
    db.refresh(grupo_a)
    db.refresh(grupo_b)

    # Seleções
    selecao_bra = models.Selecao(nome="Brasil", sigla="BRA", id_grupo=grupo_a.id_grupo)
    selecao_arg = models.Selecao(nome="Argentina", sigla="ARG", id_grupo=grupo_a.id_grupo)
    selecao_sui = models.Selecao(nome="Suíça", sigla="SUI", id_grupo=grupo_b.id_grupo)
    selecao_cat = models.Selecao(nome="Catar", sigla="CAT", id_grupo=grupo_b.id_grupo)
    selecao_can = models.Selecao(nome="Canadá", sigla="CAN", id_grupo=grupo_b.id_grupo)
    selecao_cor = models.Selecao(nome="Coreia do Sul", sigla="COR", id_grupo=grupo_a.id_grupo)
    selecao_tche = models.Selecao(nome="República Tcheca", sigla="TCH", id_grupo=grupo_a.id_grupo)
    selecao_afr = models.Selecao(nome="África do Sul", sigla="AFR", id_grupo=grupo_b.id_grupo)
    db.add_all([selecao_bra, selecao_arg, selecao_sui, selecao_cat, selecao_can, selecao_cor, selecao_tche, selecao_afr])
    db.commit()
    db.refresh(selecao_bra)
    db.refresh(selecao_arg)
    db.refresh(selecao_sui)
    db.refresh(selecao_cat)
    db.refresh(selecao_can)
    db.refresh(selecao_cor)
    db.refresh(selecao_tche)
    db.refresh(selecao_afr)

    # Partidas
    partida1 = models.Partida(
        id_fase=fase_grupos.id_fase,
        id_selecao_a=selecao_bra.id_selecao,
        id_selecao_b=selecao_arg.id_selecao,
        num_jogo=1,
        data_hora=datetime.now() + timedelta(days=1),
        status=schemas.StatusPartidaEnum.agendada,
        odd_a=1.65, odd_b=4.50, odd_empate=3.40
    )
    partida2 = models.Partida(
        id_fase=fase_grupos.id_fase,
        id_selecao_a=selecao_sui.id_selecao,
        id_selecao_b=selecao_can.id_selecao,
        num_jogo=2,
        data_hora=datetime.now() + timedelta(days=2),
        status=schemas.StatusPartidaEnum.agendada,
        odd_a=2.10, odd_b=3.10, odd_empate=3.00
    )
    partida3 = models.Partida(
        id_fase=fase_grupos.id_fase,
        id_selecao_a=selecao_cor.id_selecao,
        id_selecao_b=selecao_tche.id_selecao,
        num_jogo=3,
        data_hora=datetime.now() + timedelta(days=3),
        status=schemas.StatusPartidaEnum.agendada,
        odd_a=2.50, odd_b=2.80, odd_empate=3.20
    )
    partida4 = models.Partida(
        id_fase=fase_grupos.id_fase,
        id_selecao_a=selecao_afr.id_selecao,
        id_selecao_b=selecao_cat.id_selecao,
        num_jogo=4,
        data_hora=datetime.now() + timedelta(days=4),
        status=schemas.StatusPartidaEnum.agendada,
        odd_a=1.80, odd_b=4.00, odd_empate=3.50
    )
    partida5 = models.Partida(
        id_fase=fase_grupos.id_fase,
        id_selecao_a=selecao_sui.id_selecao,
        id_selecao_b=selecao_cat.id_selecao,
        num_jogo=5,
        data_hora=datetime.now() + timedelta(days=5),
        status=schemas.StatusPartidaEnum.agendada,
        odd_a=1.90, odd_b=3.80, odd_empate=3.30
    )
    db.add_all([partida1, partida2, partida3, partida4, partida5])
    db.commit()
    db.refresh(partida1)
    db.refresh(partida2)
    db.refresh(partida3)
    db.refresh(partida4)
    db.refresh(partida5)

    print("Dados de seed populados com sucesso.")

# --- Funções para Conta de Pontos ---
def get_conta_pontos_by_usuario_id(db: Session, id_usuario: int):
    return db.query(models.Conta_Pontos).filter(models.Conta_Pontos.id_usuario == id_usuario).first()

def get_movimentacoes_conta(db: Session, id_conta: int, skip: int = 0, limit: int = 10):
    return db.query(models.Movimentacao_Pontos).filter(
        models.Movimentacao_Pontos.id_conta == id_conta
    ).order_by(models.Movimentacao_Pontos.data_hora.desc()).offset(skip).limit(limit).all()
