# 🚀 ETL Automatizado de Dados Fundamentalistas com Apache Airflow e SQL Server

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.x-orange.svg)
![SQL Server](https://img.shields.io/badge/SQL%20Server-Integration-red.svg)
![Docker](https://img.shields.io/badge/Docker-Containerization-blue.svg)
![Libraries](https://img.shields.io/badge/Libraries-requests%2C%20beautifulsoup4%2C%20pandas%2C%20pyodbc%2C%20pendulum-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📊 Visão Geral do Projeto

Este repositório apresenta uma solução robusta e automatizada para a coleta (web scraping), tratamento e carga (ETL) de dados fundamentalistas de empresas listadas na bolsa brasileira, utilizando como fonte o site [Fundamentus](http://www.fundamentus.com.br/). A grande inovação aqui é a orquestração de todo o processo através do **Apache Airflow**, com a execução em um ambiente **Dockerizado**, e a persistência dos dados em um banco de dados **SQL Server**, incluindo a atualização de uma tabela histórica via stored procedure.

Este projeto é ideal para quem busca uma solução escalável e agendada para monitoramento de dados financeiros, combinando as melhores práticas de engenharia de dados.

## ✨ Funcionalidades Principais

*   **ETL Automatizado com Apache Airflow:** Orquestração completa do fluxo de dados, desde a extração até a carga e transformação final, garantindo execuções agendadas e monitoramento centralizado.
*   **Web Scraping Robusto:** Coleta abrangente de dados fundamentalistas para todas as ações disponíveis no Fundamentus, incluindo indicadores como P/L, VPA, Margens, Receita Líquida, EBIT e muito mais.
*   **Limpeza e Normalização de Dados:** Sanitização de nomes de colunas e conversão de valores (moedas, porcentagens, datas) para formatos numéricos e padronizados, facilitando a análise e a inserção no banco de dados.
*   **Integração com SQL Server:**
    *   Carga direta dos dados processados em uma tabela temporária no SQL Server.
    *   Execução de uma *stored procedure* no SQL Server para mover os dados recém-coletados para uma tabela histórica, garantindo a rastreabilidade e a evolução dos dados ao longo do tempo.
*   **Containerização com Docker:** Todo o ambiente (Airflow, PostgreSQL para metadados do Airflow, Redis para Celery, e o próprio ETL) é empacotado em contêineres Docker, garantindo portabilidade, isolamento e fácil implantação. Resumindo, aqui nós garantimos que quando o código for compartilhado não surja a célebre frase: "Na minha máquina roda...".
*   **Agendamento Flexível:** A DAG do Airflow pode ser configurada para rodar em qualquer frequência (diariamente, semanalmente, etc.), adaptando-se às necessidades de atualização dos dados.
*   **Logging Detalhado:** Implementação de logs que informam o progresso da coleta, avisos e erros, proporcionando transparência e auxiliando na depuração e monitoramento via interface do Airflow.
*   **Estrutura Modular:** O código é organizado em funções bem definidas, facilitando a compreensão, manutenção e possíveis extensões.

## 🤖 Como Funciona (para não programadores)

Imagine este sistema como uma equipe de robôs trabalhando em conjunto:

1.  **O Gerente (Apache Airflow):** É o cérebro da operação. Ele sabe exatamente o que precisa ser feito e quando. Ele acorda todos os dias (ou no horário que você definir) e diz: "Hora de coletar os dados das empresas!".
2.  **O Coletor de Dados (Script Python):** Este robô vai até o site do Fundamentus, encontra a lista de todas as empresas e, uma por uma, visita as páginas para "copiar" todas as informações financeiras importantes. Ele também organiza e limpa esses dados para que fiquem prontos para o próximo passo.
3.  **O Transportador (Script Python):** Assim que os dados são coletados e limpos, este robô os leva diretamente para um grande "arquivo" no seu banco de dados SQL Server. Ele primeiro limpa o arquivo antigo e depois coloca os dados mais recentes lá.
4.  **O Historiador (Stored Procedure SQL Server):** Depois que os dados novos estão no banco, o Gerente (Airflow) pede para um robô especial do SQL Server (a *stored procedure*) pegar esses dados e guardá-los em uma "biblioteca histórica", onde todas as informações de todos os dias ficam armazenadas. Isso permite que você veja como os dados mudaram ao longo do tempo.
5.  **A Caixa Mágica (Docker):** Tudo isso acontece dentro de uma "caixa mágica" chamada Docker. Essa caixa garante que todos os robôs tenham tudo o que precisam para trabalhar, sem bagunçar seu computador. É como ter um escritório completo e portátil para seus robôs.

No final, você terá um banco de dados SQL Server sempre atualizado com as informações mais recentes das empresas, e também um histórico completo para análises futuras!

## ⚙️ Configuração e Uso (para programadores)

### Pré-requisitos

*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (inclui Docker Compose) instalado em sua máquina.
*   Uma instância do [SQL Server](https://www.microsoft.com/en-us/sql-server/sql-server-downloads) acessível (pode ser local ou em nuvem).
*   Um usuário e senha para o SQL Server com permissões de `SELECT`, `INSERT`, `DELETE` na tabela de carga e `EXECUTE` na stored procedure.

### Estrutura do Projeto
