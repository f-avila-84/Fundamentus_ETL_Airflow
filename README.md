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

├── dags/ 

│ ├── fundamentus_etl_with_procedure.py # Definição da DAG do Airflow 

│ └── Fundamentus_WebScraping_Tratamento_CargaSQL.py # Lógica principal do ETL 

├── data/ # Pasta para CSVs temporários (montada como volume Docker) 

├── logs/ # Logs do Airflow (montada como volume Docker) 

├── plugins/ # Plugins do Airflow (montada como volume Docker) 

├── docker-compose.yaml # Configuração dos serviços Docker 

└── Dockerfile # (Implícito pelo docker-compose build) Para construir a imagem customizada do Airflow


### Instalação e Execução

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/f-avila-84/Fundamentus_ETL_Airflow.git
    cd Fundamentus_ETL_Airflow
    ```

2.  **Construa a Imagem Docker do Airflow e Inicie os Serviços:**
    Este comando irá construir a imagem customizada do Airflow (que incluirá as dependências Python como `requests`, `beautifulsoup4`, `pandas`, `pyodbc`, `pendulum` e o driver ODBC para SQL Server) e iniciar todos os serviços definidos no `docker-compose.yaml` (PostgreSQL, Redis, Airflow Webserver, Scheduler, Worker).

    ```bash
    docker compose up -d --build
    ```
    Aguarde alguns minutos para que todos os serviços subam e o Airflow seja inicializado.

3.  **Acesse a Interface do Airflow:**
    Abra seu navegador e acesse `http://localhost:8080`.
    As credenciais padrão são:
    *   **Usuário:** `airflow`
    *   **Senha:** `airflow`
    (Você pode alterar estas credenciais no `docker-compose.yaml` antes de iniciar os serviços).

4.  **Configure a Conexão com o SQL Server no Airflow:**
    Dentro da interface do Airflow:
    *   Vá em `Admin` -> `Connections`.
    *   Clique no botão `+` para adicionar uma nova conexão.
    *   Preencha os campos conforme abaixo:
        *   **Conn Id:** `sql_server_fundamentus_conn` (Este ID é crucial e deve ser exatamente este, pois é referenciado no código Python).
        *   **Conn Type:** `Microsoft SQL Server` (Caso não exista esta opção, selecione `Generic`)
        *   **Host:** O endereço IP ou hostname do seu SQL Server (ex: `localhost`, `192.168.1.100`, ou o nome do serviço Docker se o SQL Server estiver em outro contêiner na mesma rede).
        *   **Schema:** O nome do seu banco de dados (ex: `FundamentosDB`).
        *   **Login:** O nome de usuário para acessar o SQL Server.
        *   **Password:** A senha do usuário.
        *   **Extra:** Adicione o seguinte JSON para configurar o driver ODBC e a criptografia (ajuste o nome do driver se necessário):
            ```json
            {
              "driver": "{ODBC Driver 18 for SQL Server}",
              "encrypt": "yes",
              "trust_server_certificate": "yes"
            }
            ```
    *   Clique em `Test` para verificar a conexão e depois em `Save`.

5.  **Habilite a DAG:**
    Na página inicial do Airflow (DAGs), procure por `fundamentus_etl_with_procedure`.
    Ative a DAG clicando no botão de `toggle` (deve mudar de cinza para azul).

6.  **Execute a DAG:**
    Você pode aguardar o agendamento (`schedule_interval`) ou acionar a DAG manualmente clicando no botão `Trigger DAG` (ícone de play).

### SQL Server Schema Esperado

Para que o ETL funcione corretamente, você precisará de uma tabela de carga e uma stored procedure no seu SQL Server.

**Tabela de Carga (Exemplo):**
A tabela `carga_fundamentus` será criada ou limpa e preenchida a cada execução.
```sql
CREATE TABLE [dbo].[carga_fundamentus](
	[ticker] [varchar](max) NULL,
	[data_execucao] [date] NULL,
	[hora_execucao] [varchar](max) NULL,
	[tipo] [varchar](50) NULL,
	[empresa] [nvarchar](100) NULL,
	[setor] [nvarchar](100) NULL,
	[subsetor] [nvarchar](100) NULL,
	[data_ult_cot] [date] NULL,
	[cotacao] [float] NULL,
	[min_52_sem] [float] NULL,
	[max_52_sem] [float] NULL,
	[vol_med_2m] [float] NULL,
	[ult_balanco_processado] [date] NULL,
	[valor_de_mercado] [float] NULL,
	[valor_da_firma] [float] NULL,
	[nro_acoes] [float] NULL,
	[dia] [float] NULL,
	[pl] [float] NULL,
	[lpa] [float] NULL,
	[mes] [float] NULL,
	[pvp] [float] NULL,
	[vpa] [float] NULL,
	[30_dias] [float] NULL,
	[pebit] [float] NULL,
	[marg_bruta] [float] NULL,
	[12_meses] [float] NULL,
	[psr] [float] NULL,
	[marg_ebit] [float] NULL,
	[pativos] [float] NULL,
	[marg_liquida] [float] NULL,
	[pcap_giro] [float] NULL,
	[ebit_ativo] [float] NULL,
	[pativ_circ_liq] [float] NULL,
	[roic] [float] NULL,
	[div_yield] [float] NULL,
	[roe] [float] NULL,
	[ev_ebitda] [float] NULL,
	[liquidez_corr] [float] NULL,
	[ev_ebit] [float] NULL,
	[div_br_patrim] [float] NULL,
	[cres_rec_5a] [float] NULL,
	[giro_ativos] [float] NULL,
	[ativo] [float] NULL,
	[div_bruta] [float] NULL,
	[disponibilidades] [float] NULL,
	[div_liquida] [float] NULL,
	[ativo_circulante] [float] NULL,
	[patrim_liq] [float] NULL,
	[receita_liquida_12m] [float] NULL,
	[receita_liquida_3m] [float] NULL,
	[ebit_12m] [float] NULL,
	[ebit_3m] [float] NULL,
	[lucro_liquido_12m] [float] NULL,
	[lucro_liquido_3m] [float] NULL,
	[depositos] [float] NULL,
	[cart_de_credito] [float] NULL,
	[result_int_financ_12m] [float] NULL,
	[result_int_financ_3m] [float] NULL,
	[rec_servicos_12m] [float] NULL,
	[rec_servicos_3m] [float] NULL,
	[2010] [float] NULL,
	[2011] [float] NULL,
	[2012] [float] NULL,
	[2013] [float] NULL,
	[2014] [float] NULL,
	[2015] [float] NULL,
	[2016] [float] NULL,
	[2017] [float] NULL,
	[2018] [float] NULL,
	[2019] [float] NULL,
	[2020] [float] NULL,
	[2021] [float] NULL,
	[2022] [float] NULL,
	[2023] [float] NULL,
	[2024] [float] NULL,
	[2025] [float] NULL
); 
```

**Stored Procedure (Exemplo):** A stored procedure carga_fundamentus_historico será responsável por mover os dados da tabela de carga para sua tabela histórica, adicionando um id único e garantindo que não haja duplicatas para a mesma data de execução/ticker.

```sql
CREATE PROCEDURE [dbo].[carga_fundamentus_historico]
    AS

-- Evitar duplicidade de dados de um mesmo dia.
-- Exclui dados da tabela historica que possuam a mesma data de execução da tabela de carga.
DELETE FROM [FundamentosDB].[dbo].[fundamentus_historico]
WHERE data_execucao IN (SELECT DISTINCT data_execucao FROM [FundamentosDB].[dbo].[carga_fundamentus])

-- Insere os novos dados na tabela historica.
INSERT INTO [FundamentosDB].[dbo].[fundamentus_historico]
SELECT *
  FROM [FundamentosDB].[dbo].[carga_fundamentus]

    GO;
```


### 🤝 Contribuindo
Este é um projeto desenvolvido para fins de estudo e portfólio. No momento, não estou buscando contribuições externas. No entanto, sinta-se à vontade para fazer um fork, explorar e adaptar o código para suas necessidades!


### 📧 Autor / Contato
Desenvolvido por Felipe Avila.

[github.com](https://github.com/f-avila-84)

[linkedin.com](https://www.linkedin.com/in/avilafelipe/)



### ⚠️ Aviso Legal e Disclaimer de Investimento
Este código foi desenvolvido para fins educacionais e informativos como parte de um projeto de estudo pessoal. Ele tem como objetivo demonstrar a coleta e organização de dados fundamentalistas de forma automatizada.

É fundamental entender que as informações obtidas através deste script NÃO constituem aconselhamento financeiro, recomendação de investimento ou endosso de qualquer tipo de estratégia de investimento. O mercado financeiro é complexo e investimentos envolvem riscos, incluindo a possibilidade de perda de capital.

Não se baseie unicamente nos dados gerados por este código para tomar decisões de investimento.
Retornos passados não são garantia de retornos futuros.
Qualquer decisão de investimento é de sua inteira responsabilidade.
Recomenda-se sempre consultar um profissional financeiro qualificado antes de tomar qualquer decisão de investimento. O desenvolvedor deste código não se responsabiliza por quaisquer perdas ou prejuízos decorrentes do uso ou interpretação das informações aqui contidas.

### 📜 Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 

[opensource.org](https://opensource.org/license/mit)





