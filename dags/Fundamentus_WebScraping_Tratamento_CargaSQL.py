import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import unicodedata
import concurrent.futures
import random
import pyodbc
import logging
from airflow.hooks.base import BaseHook # Importação necessária para Airflow
import pendulum # Importação necessária para Airflow (e boa prática para datas)

# --- Configuração do Servidor MS SQL ---
# Estas variáveis serão usadas como fallback ou para referência,
# mas o Airflow usará as configurações da conexão definida na UI.
servidor = 'DESKTOP'
banco_de_dados = 'FundamentosDB'
driver_obdc_sql = '{ODBC Driver 18 for SQL Server}'
tabela_sql = 'carga_fundamentus'
conexao_autenticacao_windows = True # Se você usa autenticação Windows
nome_de_usuario_sql = None
senha_usuario_sql = None

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Iniciando a coleta de dados fundamentalistas do Fundamentus...")

BASE_URL = "http://www.fundamentus.com.br/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- Função auxiliar para normalizar strings (remove acentos, caracteres diacríticos, espaços extras, etc.) ---
def normalize_string_for_comparison(s: str) -> str:
    # REMOVE O CARACTERE '?' INICIAL SE EXISTIR
    if s.startswith('?'):
        s = s[1:]
    # Remove acentos e caracteres diacríticos
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8').strip()
    # Troca espaços não quebráveis por espaços normais
    s = s.replace('\xa0', ' ').strip()
    # Remove múltiplos espaços e garante um único espaço entre as palavras
    s = ' '.join(s.split())
    return s

# --- LISTAS RAW: Strings EXATAS como aparecem no site (antes de remover ':') ---
STRING_FIELDS_RAW = [
    "Tipo:",
    "Empresa:",
    "Setor:",
    "Subsetor:",
    "Data últ cot:", 
    "Últ balanço processado:", 
]

SPECIAL_METRICS_RAW = [
    "Receita Líquida:",
    "EBIT:",
    "Lucro Líquido:",
    "Result Int Financ:",
    "Rec Serviços:",
]

# --- NORMALIZAÇÃO DAS LISTAS UMA ÚNICA VEZ NO INÍCIO DO SCRIPT ---
STRING_FIELDS = [normalize_string_for_comparison(s.replace(":", "")) for s in STRING_FIELDS_RAW]
SPECIAL_METRICS = [normalize_string_for_comparison(s.replace(":", "")) for s in SPECIAL_METRICS_RAW]

# --- Lista de colunas que devem ser convertidas para DATE no SQL Server ---
# Estes são os nomes das colunas APÓS a limpeza por clean_column_name
DATE_COLUMNS_TO_CONVERT = [
    "data_ult_cot",
    "ult_balanco_processado"
]

def clean_and_convert_value(value_str):
    """
    Limpa e converte uma string para um valor numérico (float),
    tratando moedas, porcentagens e separadores decimais.
    """
    if isinstance(value_str, (int, float)):
        return value_str
    
    value_str = str(value_str).strip() # Garante que é string
    value_str = value_str.replace("R\$", "").replace("%", "").replace(".", "").replace(",", ".").strip()
    
    try:
        float_val = float(value_str)
        return float_val
    except ValueError:
        return pd.NA

# 1) Alterar os nomes das colunas para retirar os caracteres especiais
def clean_column_name(col_name: str) -> str:
    """
    Limpa o nome de uma coluna, removendo acentos, caracteres especiais,
    substituindo espaços por underscores e convertendo para minúsculas.
    """
    # Normaliza caracteres Unicode (ex: 'ç' -> 'c', 'é' -> 'e')
    cleaned_name = unicodedata.normalize('NFKD', col_name).encode('ascii', 'ignore').decode('utf-8')
    # Substitui espaços e hifens por underscores
    cleaned_name = cleaned_name.replace(' ', '_').replace('-', '_')
    # Remove qualquer caractere que não seja letra, número ou underscore
    cleaned_name = re.sub(r'[^a-zA-Z0-9_]', '', cleaned_name)
    # Remove underscores duplicados ou no início/fim
    cleaned_name = re.sub(r'_+', '_', cleaned_name).strip('_')
    # Converte para minúsculas
    cleaned_name = cleaned_name.lower()
    return cleaned_name

def scrape_company_data(ticker: str) -> dict:
    """
    Coleta dados de uma única empresa no Fundamentus.
    """
    url = f"{BASE_URL}detalhes.php?papel={ticker}"
    company_data = {"Ticker": ticker}

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status() # Lança exceção para status HTTP de erro
    except requests.exceptions.RequestException as e:
        logging.warning(f"  Erro ao acessar a página de {ticker}: {e}")
        return company_data

    soup = BeautifulSoup(response.text, "html.parser")

    label_tds = soup.find_all("td", class_="label")
    
    for label_tag in label_tds:
        raw_label_from_html = label_tag.text.strip()
        
        # Remove o ':' e então normaliza para comparação e uso como chave
        processed_label_no_colon = raw_label_from_html.replace(":", "")
        normalized_label = normalize_string_for_comparison(processed_label_no_colon)

        # Este bloco é para SPECIAL_METRICS (Receita Líquida, EBIT, etc.)
        if normalized_label in SPECIAL_METRICS:
            parent_row = label_tag.find_parent("tr")
            if parent_row:
                data_cells = parent_row.find_all("td", class_="data")
                if len(data_cells) >= 2:
                    value_12m = data_cells[0].text.strip()
                    value_3m = data_cells[1].text.strip()

                    # Adiciona ao dicionário com os nomes normalizados e sufixos
                    company_data[f"{normalized_label} 12m"] = value_12m
                    company_data[f"{normalized_label} 3m"] = value_3m
        else:
            data_tag = label_tag.find_next_sibling("td", class_="data")
            if data_tag:
                value = data_tag.text.strip()
                company_data[normalized_label] = value # Usa o nome normalizado como chave
    
    # Após popular company_data, processa os valores
    for key, value in company_data.items():
        # Verifica se a chave (label normalizado) está em STRING_FIELDS
        # E também não converte colunas que serão tratadas como datas
        if key != "Ticker" and key not in STRING_FIELDS and clean_column_name(key) not in DATE_COLUMNS_TO_CONVERT:
            company_data[key] = clean_and_convert_value(value)

    time.sleep(random.uniform(0.1, 0.5)) # Pequeno delay para evitar sobrecarga no servidor
    return company_data

def get_all_tickers() -> list:
    """
    Obtém a lista de todos os tickers de empresas disponíveis no Fundamentus.
    """
    logging.info("Obtendo lista de todos os tickers do Fundamentus...")
    tickers = []
    try:
        response = requests.get(f"{BASE_URL}resultado.php", headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        table = soup.find("table", class_="resultado")
        
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]: # Ignora a linha de cabeçalho
                cols = row.find_all("td")
                if cols and cols[0].find('a'): # Verifica se a primeira coluna contém um link (um ticker)
                    ticker = cols[0].text.strip()
                    tickers.append(ticker)
        else:
            logging.warning("    AVISO: Tabela de resultados não encontrada na página de tickers.")
    except requests.exceptions.RequestException as e:
        logging.error(f"  Erro ao acessar a página de resultados para obter tickers: {e}")
    
    logging.info(f"  {len(tickers)} tickers encontrados.")
    return tickers

def save_to_sql_sqlserver_pyodbc(
        df: pd.DataFrame,
        table_name: str,
        server: str, # Parâmetros agora são obrigatórios para a função
        db_name: str,
        driver: str = '{ODBC Driver 18 for SQL Server}', # Driver padrão
        trusted_connection: bool = False, # Padrão para False, Airflow geralmente usa user/pass
        username: str = None,
        password: str = None
    ) -> None:
    """
    Salva o DataFrame em um banco de dados SQL Server usando pyodbc diretamente.
    Esta função está otimizada para autenticação Windows (trusted_connection=True).
    """
    logging.info(f"\nIniciando a integração com o SQL Server na tabela '{table_name}' usando pyodbc direto...")

    if df.empty:
        logging.warning("DataFrame vazio, nada para salvar no banco de dados.")
        return

    # --- Construção da string de conexão para pyodbc ---
    conn_str_parts = []
    conn_str_parts.append(f'DRIVER={driver}')
    conn_str_parts.append(f'SERVER={server}')
    conn_str_parts.append(f'DATABASE={db_name}')

    if trusted_connection:
        conn_str_parts.append('Trusted_Connection=yes')
    else:
        if username and password:
            conn_str_parts.append(f'UID={username}')
            conn_str_parts.append(f'PWD={password}')
        else:
            logging.error("Para trusted_connection=False, 'username' e 'password' devem ser fornecidos.")
            raise ValueError("Credenciais de usuário/senha SQL Server ausentes.")
    
    # Adicionar parâmetros de criptografia e confiança para o ODBC Driver 18
    conn_str_parts.append('Encrypt=yes')
    conn_str_parts.append('TrustServerCertificate=yes')

    pyodbc_conn_str = ';'.join(conn_str_parts)

    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(pyodbc_conn_str)
        cursor = conn.cursor()

        # 1. Limpar a tabela (DELETE)
        logging.info(f"  Limpando dados existentes na tabela '{table_name}'...")
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit() # Commit explícito para o DELETE
        logging.info(f"  Tabela '{table_name}' limpa com sucesso.")

        # 2. Inserir os novos dados (INSERT)
        logging.info(f"  Iniciando inserção de {len(df)} registros na tabela '{table_name}'...\n")

        # Preparar a instrução INSERT
        # IMPORTANTE: Delimitar os nomes das colunas com colchetes [] para SQL Server
        # Isso resolve o erro de sintaxe para nomes como '30_dias'
        quoted_columns = [f"[{col}]" for col in df.columns]
        columns = ', '.join(quoted_columns)
        placeholders = ', '.join(['?' for _ in df.columns]) # '?' é o placeholder para pyodbc
        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # Converter DataFrame para uma lista de tuplas para executemany
        # Tratar valores NaN/NaT do Pandas para None (NULL no SQL)
        data_to_insert = []
        for row in df.itertuples(index=False, name=None):
            # Converte pd.NA, pd.NaT, e np.nan para None para compatibilidade com o banco de dados
            cleaned_row = tuple(None if pd.isna(x) else x for x in row)
            data_to_insert.append(cleaned_row)

        cursor.executemany(insert_sql, data_to_insert)
        conn.commit() # Commit explícito para o INSERT
        logging.info(f"  Dados inseridos com sucesso na tabela '{table_name}'.")

    except pyodbc.Error as e:
        sqlstate = e.args[0]
        logging.error(f"  Erro de banco de dados pyodbc: {e}")
        logging.error(f"  SQLSTATE: {sqlstate}")
        if conn:
            conn.rollback() # Faz rollback em caso de erro
        raise # Re-lança a exceção
    except Exception as e:
        logging.error(f"  Erro inesperado ao salvar dados no SQL Server: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logging.info("  Conexão pyodbc fechada.")


###################################################################################################################
# NOVO BLOCO, VERIFICAR SE FICOU NO LUGAR CORRETO #################################################################
###################################################################################################################

def execute_sql_procedure(
        procedure_name: str,
        conn_id: str = 'sql_server_fundamentus_conn', # ID da conexão Airflow
        driver: str = '{ODBC Driver 18 for SQL Server}'
    ) -> None:
    """
    Conecta ao SQL Server e executa uma procedure armazenada.
    Os detalhes da conexão são obtidos do Airflow Connections.
    """
    logging.info(f"\nIniciando execução da procedure '{procedure_name}' no SQL Server...")

    conn = None
    cursor = None
    try:
        # Obter detalhes da conexão do Airflow
        airflow_conn = BaseHook.get_connection(conn_id)

        server = airflow_conn.host
        db_name = airflow_conn.schema # No Airflow, 'Schema' é usado para o nome do banco de dados
        username = airflow_conn.login
        password = airflow_conn.password

        # Determinar se deve usar Trusted_Connection ou Autenticação SQL Server
        trusted_connection = not (username and password)

        # Construção da string de conexão para pyodbc
        conn_str_parts = []
        conn_str_parts.append(f'DRIVER={driver}')
        conn_str_parts.append(f'SERVER={server}')
        conn_str_parts.append(f'DATABASE={db_name}')

        if trusted_connection:
            conn_str_parts.append('Trusted_Connection=yes')
        else:
            conn_str_parts.append(f'UID={username}')
            conn_str_parts.append(f'PWD={password}')
        
        conn_str_parts.append('Encrypt=yes')
        conn_str_parts.append('TrustServerCertificate=yes')

        pyodbc_conn_str = ';'.join(conn_str_parts)

        conn = pyodbc.connect(pyodbc_conn_str)
        cursor = conn.cursor()

        # Executar a procedure
        logging.info(f"  Executando CALL {procedure_name}...")
        cursor.execute(f"{{CALL {procedure_name}}}") # Sintaxe para chamar procedures em ODBC
        conn.commit()
        logging.info(f"  Procedure '{procedure_name}' executada com sucesso.")

    except pyodbc.Error as e:
        sqlstate = e.args[0]
        logging.error(f"  Erro de banco de dados pyodbc ao executar procedure: {e}")
        logging.error(f"  SQLSTATE: {sqlstate}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logging.error(f"  Erro inesperado ao executar procedure '{procedure_name}': {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logging.info("  Conexão pyodbc para procedure fechada.")



# --- Função principal para ETL (compatível com Apache Airflow) ---
def etl_fundamentus_data(**kwargs): # <--- ESSENCIAL para Airflow
    """
    Função principal que orquestra o processo de ETL (Extração, Transformação, Carga)
    dos dados fundamentalistas do Fundamentus.
    Projetada para ser chamada por um PythonOperator no Apache Airflow.
    """
    start_time = time.time()

    # --- Obter e ajustar o timestamp de execução para o fuso horário de Brasília ---
    # Airflow passa 'data_interval_start' ou 'execution_date'
    execution_date_utc = kwargs.get('data_interval_start') or kwargs.get('execution_date')

    if execution_date_utc:
        brasilia_tz = pendulum.timezone('America/Sao_Paulo')
        # Converte o timestamp do Airflow para o fuso horário de Brasília
        timestamp_brt = execution_date_utc.in_timezone(brasilia_tz) 

        logging.info(f"Data/Hora de execução (UTC): {execution_date_utc.isoformat()}")
        logging.info(f"Data/Hora de execução (BRT): {timestamp_brt.isoformat()}")
    else:
        # Fallback para quando a função é executada fora do contexto do Airflow (ex: teste local)
        # Embora este script seja para Airflow, é bom ter um fallback robusto.
        timestamp_brt = pendulum.now('America/Sao_Paulo')
        logging.info(f"Execução fora do contexto Airflow, usando data/hora atual (BRT): {timestamp_brt.isoformat()}")

    # Use timestamp_brt para o nome do arquivo CSV e para a coluna 'Data_Execucao'
    # String ISO formatada com fuso horário (removido, pois o replace(tzinfo=None) já faz isso)

    # --- Extração ---
    all_tickers = get_all_tickers() 
    if not all_tickers:
        logging.error("Nenhum ticker encontrado. Encerrando o processo ETL.")
        return pd.DataFrame() 

    all_companies_data = []
    MAX_WORKERS = 8 
    
    logging.info(f"\nIniciando coleta de dados para {len(all_tickers)} empresas usando {MAX_WORKERS} threads...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_company_data, ticker): ticker for ticker in all_tickers}
        
        processed_count = 0
        for future in concurrent.futures.as_completed(futures):
            ticker = futures[future]
            try:
                data = future.result()
                if data:
                    # Adiciona o timestamp de execução a cada registro
                    # O timestamp_brt é um objeto pendulum, que pd.to_datetime pode converter
                    data['Data_Execucao'] = timestamp_brt.replace(tzinfo=None) # Passa o objeto datetime sem tzinfo
                    all_companies_data.append(data)
            except Exception as exc:
                logging.error(f"  Ticker {ticker} gerou uma exceção durante scraping: {exc}")
            processed_count += 1
            if processed_count % 50 == 0 or processed_count == len(all_tickers):
                logging.info(f"Progresso de scraping: {processed_count}/{len(all_tickers)} empresas processadas.")

    logging.info("\nColeta de dados concluída. Criando DataFrame...")
    df = pd.DataFrame(all_companies_data)
    
    # --- Transformação ---

    # 1) Alterar os nomes das colunas
    original_columns = df.columns.tolist()
    df.columns = [clean_column_name(col) for col in df.columns]
    logging.info(f"Nomes das colunas alterados. Exemplo original: {original_columns[:3]} -> Limpos: {df.columns.tolist()[:3]}")

    # --- NOVO PASSO: Conversão de colunas de data para formato 'YYYY-MM-DD' ---
    for col_name in DATE_COLUMNS_TO_CONVERT:
        if col_name in df.columns:
            # Explicitamente substitui '-' (e outros valores que podem indicar nulo) por pd.NA
            # Isso garante que esses valores sejam tratados como ausentes antes da conversão de data.
            # Você pode adicionar outros valores aqui se necessário, como 'N/A', '', etc.
            df[col_name] = df[col_name].replace(['-', ''], pd.NA) # Adicionado '' para strings vazias
            
            # Converte para objetos datetime. Datas inválidas se tornam NaT (Not a Time).
            # O formato de entrada é DD/MM/YYYY.
            df[col_name] = pd.to_datetime(df[col_name], format='%d/%m/%Y', errors='coerce')
            
            # Formata para 'YYYY-MM-DD' para compatibilidade com o tipo DATE do SQL Server.
            # Valores NaT (datas inválidas) são convertidos para None.
            df[col_name] = df[col_name].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)
            logging.info(f"  Coluna '{col_name}' convertida para formato 'YYYY-MM-DD' ou None.")
        else:
            logging.warning(f"  Coluna de data '{col_name}' não encontrada no DataFrame para conversão.")

    # Remover colunas específicas, agora usando os nomes limpos
    if 'papel' in df.columns:
        df.drop(columns=['papel'], inplace=True)
        logging.info("  Coluna 'papel' removida.")
    
    original_cols_count = df.shape[1]
    df.dropna(axis=1, how='all', inplace=True) # Remove colunas totalmente vazias
    if df.shape[1] < original_cols_count:
        logging.info(f"  {original_cols_count - df.shape[1]} colunas totalmente vazias removidas.\n")

    # Colunas numéricas que não são afetadas pela limpeza de nome, mas podem ser removidas se necessário
    cols_to_drop_by_name = ['1', '2', '3', '4'] 
    existing_cols_to_drop = [col for col in cols_to_drop_by_name if col in df.columns]
    if existing_cols_to_drop:
        df.drop(columns=existing_cols_to_drop, inplace=True)
        logging.info(f"  Colunas {existing_cols_to_drop} removidas.\n")

    # 2) Dividir 'data_execucao' em 'data_execucao' (apenas data) e 'hora_execucao'
    if 'data_execucao' in df.columns:
        df['data_execucao'] = pd.to_datetime(df['data_execucao']) # Garante que é datetime para manipulação
        df['hora_execucao'] = df['data_execucao'].dt.strftime('%H:%M:%S') # Extrai apenas a hora
        df['data_execucao'] = df['data_execucao'].dt.strftime('%Y-%m-%d') # Formata 'data_execucao' como 'YYYY-MM-DD'
        logging.info("  Coluna 'data_execucao' dividida em 'data_execucao' (somente data) e 'hora_execucao'.\n")
    else:
        logging.warning("  Coluna 'data_execucao' não encontrada para divisão de data/hora.\n")

    # Reordenar colunas com os novos nomes limpos e a nova coluna 'hora_execucao'
    current_columns = df.columns.tolist()
    year_columns = []
    other_columns = []
    
    for col in current_columns:
        # Regex para anos: Apenas 4 dígitos numéricos (como '2020')
        if re.fullmatch(r'\d{4}', col) and 1900 <= int(col) <= 2100: 
            year_columns.append(col)
        else:
            other_columns.append(col)
            
    year_columns.sort(key=int) 
    
    final_column_order = []
    # Posicionar 'ticker', 'data_execucao' e 'hora_execucao' no início
    if 'ticker' in other_columns:
        final_column_order.append('ticker')
        other_columns.remove('ticker')
    
    if 'data_execucao' in other_columns:
        final_column_order.append('data_execucao')
        other_columns.remove('data_execucao')

    if 'hora_execucao' in other_columns:
        final_column_order.append('hora_execucao')
        other_columns.remove('hora_execucao')
    
    final_column_order.extend(other_columns) 
    final_column_order.extend(year_columns)  
    
    df = df[final_column_order] 
    
    logging.info("\nDataFrame final após transformações. Primeiras 5 linhas:")
    logging.info(f"\n{df.head().to_string()}") 
    
    logging.info("\nInformações do DataFrame final:")
    df.info()

    # 3) Salvar CSV com nome dinâmico
    try:
        csv_filename = f"carga_fundamentus_{timestamp_brt.strftime('%Y%m%d_%H%M%S')}.csv"
        csv_filepath = f"data/{csv_filename}" 
        df.to_csv(csv_filepath, index=False, encoding="utf-8-sig")
        logging.info(f"\nDados salvos em '{csv_filepath}'")
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo CSV: {e}")

    # --- Carga (Load) ---
    try:
        # O ID da conexão que você criou na UI do Airflow
        conn_id = 'sql_server_fundamentus_conn' # Certifique-se que este ID existe na sua UI do Airflow
        conn = BaseHook.get_connection(conn_id)

        sql_server_host = conn.host
        sql_server_db = conn.schema # No Airflow, o campo 'Schema' é usado para o nome do banco de dados
        sql_server_login = conn.login
        sql_server_password = conn.password

        # Determinar se deve usar Trusted_Connection ou Autenticação SQL Server
        # Se login e senha forem fornecidos na conexão do Airflow, usa SQL Server Auth.
        # Caso contrário, tenta Trusted_Connection (Autenticação Windows).
        # ATENÇÃO: Autenticação Windows (Trusted_Connection) é mais complexa em Docker.
        # Recomenda-se usar autenticação SQL Server (usuário/senha) para Docker.
        use_trusted_connection = not (sql_server_login and sql_server_password)

        # --- Chamar a função save_to_sql_sqlserver_pyodbc com os parâmetros obtidos ---
        save_to_sql_sqlserver_pyodbc(
            df,
            table_name=tabela_sql,
            server=sql_server_host,
            db_name=sql_server_db,
            trusted_connection=use_trusted_connection,
            username=sql_server_login,
            password=sql_server_password
        )
        logging.info("Carga de dados para o SQL Server concluída com sucesso!")

    except Exception as e:
        logging.error(f"Falha fatal ao carregar dados para o SQL Server: {e}")
        raise # Re-lança a exceção para o Airflow marcar a tarefa como falha

    end_time = time.time() 
    total_time = end_time - start_time 
    logging.info(f"\nProcesso ETL finalizado em {total_time:.2f} segundos. ✅") 

    return df 

# --- Bloco de execução principal (para testes locais, fora do Airflow) ---
# Este bloco NÃO será executado quando o script for carregado como uma DAG pelo Airflow.
# Ele é útil apenas para testar a função etl_fundamentus_data isoladamente.
if __name__ == "__main__":
    logging.warning("Executando o script diretamente. Isso não simula o ambiente Airflow completo.")
    # Para testar localmente, você pode chamar a função sem argumentos.
    # A lógica de fallback do timestamp_brt será ativada.
    # A conexão com o SQL Server precisará ser ajustada manualmente ou mockada para testes.
    # etl_fundamentus_data() # Descomente para testar localmente, mas a conexão SQL via BaseHook falhará.
    logging.warning("Para testar a lógica de ETL localmente (sem Airflow e sem conexão SQL via BaseHook), use a versão do script que remove as dependências do Airflow.")