from datetime import datetime

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = "/opt/airflow/project"
DBT = "/home/airflow/dbt-venv/bin/dbt"
PYTHON = "/home/airflow/dbt-venv/bin/python"

with DAG(
    dag_id="vietjobs_pipeline",
    description="Load VietJobs CSV, transform data with dbt, and run data tests",
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Ho_Chi_Minh"),
    schedule=None,
    catchup=False,
    default_args={
        "owner": "data-engineering",
        "retries": 1,
    },
    tags=["vietjobs", "data-pipeline"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_vietjobs",
        bash_command=(
            f"cd {PROJECT} && "
            f"{PYTHON} src/ingestion/load_vietjobs.py --replace"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd {PROJECT} && "
            f"{DBT} run "
            "--project-dir vietjobs_dbt "
            "--profiles-dir ."
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {PROJECT} && "
            f"{DBT} test "
            "--project-dir vietjobs_dbt "
            "--profiles-dir ."
        ),
    )

    ingest >> dbt_run >> dbt_test
