FROM apache/airflow:2.10.5-python3.11

USER airflow

RUN python -m venv /home/airflow/dbt-venv && \
    /home/airflow/dbt-venv/bin/pip install \
    --no-cache-dir \
    --retries 10 \
    --timeout 120 \
    "psycopg[binary]==3.3.6" \
    "dbt-core==1.12.5" \
    "dbt-postgres==1.11.0"
