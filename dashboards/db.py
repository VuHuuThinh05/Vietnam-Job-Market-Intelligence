"""Connection factory for local PostgreSQL queries."""
import os
import psycopg


def get_connection():
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise RuntimeError("DB_PASSWORD is required; export it before launching Streamlit.")
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "vietjobs"),
        user=os.getenv("DB_USER", "vietjobs"),
        password=password,
    )
