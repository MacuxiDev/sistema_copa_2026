# ⚽ Sistema de Apostas - Copa 2026

Este projeto implementa o core de um sistema de apostas esportivas focado na Copa do Mundo de 2026. Desenvolvido em Python, utiliza SQLAlchemy para modelagem e persistência de dados em um banco SQLite, e Pydantic para validação de dados. O sistema abrange desde a gestão de dados mestres (fases, grupos, seleções, partidas) até funcionalidades complexas de apostas, liquidação de resultados e um ranking de usuários.

## 🚀 Funcionalidades Principais

O sistema oferece as seguintes funcionalidades, implementadas e testadas:

1.  **Gestão de Dados Mestres:**
    *   **Fases da Competição:** Cadastro e organização das fases (Grupos, Oitavas, Quartas, etc.).
    *   **Grupos e Seleções:** Definição dos grupos e das seleções participantes da Copa 2026.
    *   **Partidas:** Geração e gestão de partidas, incluindo informações como seleções, data/hora, status, gols e odds.

2.  **Gestão de Usuários e Contas:**
    *   **Cadastro de Usuários:** Criação de novos usuários com validações robustas (CPF, email, login único).
    *   **Contas de Pontos:** Cada usuário possui uma conta de pontos para realizar apostas, com saldo inicial de bônus.
    *   **Recarga de Pontos:** Funcionalidade para adicionar pontos à conta do usuário.

3.  **Gestão de Apostas:**
    *   **Criação de Apostas:** Usuários podem apostar em partidas agendadas ou ao vivo, escolhendo um palpite (vitória da seleção A, empate ou vitória da seleção B) e o valor em pontos.
    *   **Multiplicadores:** Suporte a multiplicadores de aposta.
    *   **Validação de Saldo:** Verificação automática de saldo antes de aceitar uma aposta.
    *   **Listagem de Apostas:** Consulta do histórico de apostas de um usuário.

4.  **Liquidação de Partidas e Apostas:**
    *   **Liquidação de Partidas:** Processamento dos resultados de uma partida (gols das seleções) para determinar o resultado final (vitória A, empate, vitória B).
    *   **Atualização de Apostas:** Após a liquidação da partida, as apostas associadas são atualizadas para `ganha`, `perdida` ou `reembolsada`, e os pontos são creditados/debitados nas contas dos usuários.
    *   **Cancelamento de Partidas:** Funcionalidade para cancelar uma partida, reembolsando todas as apostas ativas.

5.  **Ranking de Usuários:**
    *   **VIEW de Ranking:** Uma visão materializada (`ranking_geral`) no banco de dados que calcula e agrega estatísticas de cada usuário.
    *   **Consulta de Ranking:** Função para consultar o ranking dos usuários, ordenado por saldo, incluindo informações como apostas ganhas, perdidas, ativas, reembolsadas e taxa de acerto.

## 🛠️ Tecnologias Utilizadas

*   **Python:** Linguagem de programação principal.
*   **SQLAlchemy:** ORM (Object-Relational Mapper) para interação com o banco de dados.
*   **SQLite:** Banco de dados leve e embutido, ideal para desenvolvimento e testes.
*   **Pydantic:** Biblioteca para validação de dados e gerenciamento de configurações, utilizada para tipagem e validação de entradas.
*   **Passlib:** Para hashing seguro de senhas.
*   **Jupyter/Colab Notebooks:** Ambiente de desenvolvimento interativo para prototipagem e testes.

## 📂 Estrutura do Projeto (Core)

O projeto é organizado em células de notebook, cada uma responsável por uma parte específica do sistema:

*   **Célula 1:** Instalação de dependências (`pip install`).
*   **Célula 2:** Configuração do `engine` SQLAlchemy e `Base` declarativa.
*   **Célula 3:** Definição de todos os modelos (tabelas) do banco de dados (`Fase`, `Grupo`, `Selecao`, `Partida`, `Usuario`, `Conta_Pontos`, `Aposta`, `Movimentacao_Pontos`).
*   **Célula 4:** Seed inicial de dados mestres (Fases, Grupos, Seleções da Copa 2026).
*   **Célula 5:** Seed de 72 partidas da fase de grupos com odds simuladas.
*   **Célula 6:** Funções de gestão de usuários (criar, login, validar CPF/senha).
*   **Célula 7:** Funções de gestão de contas de pontos (criar, recarregar).
*   **Célula 8:** Seed de um usuário de teste (`conta_teste_2026`).
*   **Célula 9:** Funções de liquidação de partidas e apostas (`liquidar_partida`, `cancelar_partida`, `consultar_resultado_partida`).
*   **Célula 10:** Funções de criação e listagem de apostas (`criar_aposta`, `listar_apostas_usuario`).
*   **Célula 11:** Testes unitários e de integração para as funções de liquidação.
*   **Célula 12:** Criação da VIEW `ranking_geral` e da função `consultar_ranking`.
*   **Célula 13:** Bateria de testes completos de ponta a ponta, validando a integração de todas as funcionalidades.

## 📈 Próximos Passos

Com o core do sistema e a lógica de negócio validados, a próxima etapa natural é construir um **back-end (API)** para expor essas funcionalidades. A recomendação é utilizar o **FastAPI** devido à sua performance, facilidade de uso e excelente integração com Pydantic e SQLAlchemy.

O desenvolvimento do back-end incluirá:

*   Definição de endpoints para todas as operações.
*   Implementação de autenticação e autorização.
*   Gerenciamento de sessões de banco de dados por requisição.
*   Estruturação do projeto para deploy.
