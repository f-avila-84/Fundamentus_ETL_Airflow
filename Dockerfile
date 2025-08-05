# Use a imagem oficial do Airflow como base
# Verifique a versão do Airflow e Python que você usa
FROM apache/airflow:2.8.1-python3.10 

# Instalar dependências para o driver ODBC no Debian/Ubuntu
# (A imagem do Airflow é baseada em Debian/Ubuntu)
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc-dev \
    gnupg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Adicionar o repositório Microsoft para o driver ODBC do SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Instalar o driver ODBC do SQL Server
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql18 \
    mssql-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar pyodbc
USER airflow
RUN pip install --no-cache-dir pyodbc