from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import pendulum

# Importa a função etl_fundamentus_data e execute_sql_procedure do seu script principal
# Certifique-se que o caminho está correto para o seu ambiente Docker
# Se Fundamentus_WebScraping_Tratamento_CargaSQL.py estiver na mesma pasta dags, basta o nome do arquivo.
from Fundamentus_WebScraping_Tratamento_CargaSQL import etl_fundamentus_data, execute_sql_procedure

# Definição da DAG
with DAG(
    dag_id='fundamentus_etl_with_procedure',
    start_date=pendulum.datetime(2023, 1, 1, tz="America/Sao_Paulo"), # Data de início da DAG
    schedule_interval=None, # Defina 'None' para DAGs que são acionadas manualmente ou '@daily', '@hourly' etc.
    catchup=False, # Não executa DAGs para datas passadas
    tags=['etl', 'fundamentus', 'sqlserver'],
    doc_md="""
    ### DAG de ETL para dados fundamentalistas do Fundamentus.
    Coleta dados, carrega para o SQL Server e executa uma procedure de transformação.
    """,
) as dag:
    # Tarefa 1: Coleta, Transformação e Carga Inicial
    extract_transform_load_task = PythonOperator(
        task_id='extract_transform_load_fundamentus',
        python_callable=etl_fundamentus_data,
        # op_kwargs={'data_interval_start': '{{ ds }}'}, # Exemplo de como passar kwargs se necessário
    )

    # Tarefa 2: Executar a Procedure SQL
    # Substitua 'sua_procedure_de_transformacao' pelo nome real da sua procedure no SQL Server
    execute_procedure_task = PythonOperator(
        task_id='execute_sql_procedure',
        python_callable=execute_sql_procedure,
        op_kwargs={'procedure_name': 'carga_fundamentus_historico'}, # Passe o nome da sua procedure aqui
    )

    # Definir a ordem das tarefas
    extract_transform_load_task >> execute_procedure_task