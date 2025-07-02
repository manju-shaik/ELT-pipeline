from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from google.cloud import storage
import pandas as pd
import io

# Constants
BUCKET_NAME = 'firstdfbkt'

FILES = [
    {
        "source_path": "rawdata/Customer_Table.csv",
        "target_path": "cleaned/customer_cleaned.csv"
    },
    {
        "source_path": "rawdata/Transaction_Table.csv",
        "target_path": "cleaned/transaction_cleaned.csv"
    }
]

# Data cleaning function
def clean_csv_from_gcs(source_path, target_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    blob = bucket.blob(source_path)
    if not blob.exists():
        raise FileNotFoundError(f"File not found: gs://{BUCKET_NAME}/{source_path}")

    content = blob.download_as_bytes()
    df = pd.read_csv(io.BytesIO(content))

    # Clean headers
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df.fillna("Unknown", inplace=True)

    # Parse dates if any
    for col in df.columns:
        if 'date' in col:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Upload cleaned file to GCS
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    cleaned_blob = bucket.blob(target_path)
    cleaned_blob.upload_from_string(buffer.getvalue(), content_type='text/csv')

# Generate task dynamically
def generate_cleaning_task(file_config):
    return lambda: clean_csv_from_gcs(file_config["source_path"], file_config["target_path"])

# Define DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 6, 29),
    'retries': 1,
}

with DAG(
    dag_id='gcs_clean_and_dbt_run_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['dbt', 'gcs', 'bigquery'],
) as dag:

    # GCS cleaning tasks
    cleaning_tasks = []
    for file_conf in FILES:
        task_id = f'clean_{file_conf["source_path"].split("/")[-1].replace(".csv", "")}'
        task = PythonOperator(
            task_id=task_id,
            python_callable=generate_cleaning_task(file_conf)
        )
        cleaning_tasks.append(task)

    # dbt tasks
    dbt_debug = BashOperator(
        task_id='dbt_debug',
        bash_command="""
        cd /home/airflow/gcs/data/dbt-project && \
        dbt debug --profiles-dir . --project-dir .
        """,
    )

    run_create_external_table = BashOperator(
        task_id='run_create_external_table',
        bash_command="""
        cd /home/airflow/gcs/data/dbt-project && \
        dbt run-operation create_external_customers --profiles-dir . --project-dir .
        """,
    )

    run_create_external_transaction_table = BashOperator(
        task_id='run_create_external_transaction_table',
        bash_command="""
        cd /home/airflow/gcs/data/dbt-project && \
        dbt run-operation create_external_transaction --profiles-dir . --project-dir .
        """,
    )

    run_final_customers_model = BashOperator(
        task_id='run_final_customers_model',
        bash_command="""
        cd /home/airflow/gcs/data/dbt-project && \
        dbt run --select final_customers --profiles-dir . --project-dir .
        """,
    )

    run_final_transaction_model = BashOperator(
        task_id='run_final_transaction_model',
        bash_command="""
        cd /home/airflow/gcs/data/dbt-project && \
        dbt run --select final_transcation --profiles-dir . --project-dir .
        """,
    )

    # Define task dependencies
    for cleaning_task in cleaning_tasks:
        cleaning_task >> dbt_debug

    dbt_debug >> run_create_external_table >> run_create_external_transaction_table
    run_create_external_transaction_table >> run_final_customers_model
    run_create_external_transaction_table >> run_final_transaction_model
