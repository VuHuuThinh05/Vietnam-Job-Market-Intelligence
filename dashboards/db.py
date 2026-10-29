import os
import psycopg

def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "vietjobs"),
        user=os.getenv("DB_USER", "vietjobs"),
        password=os.getenv("DB_PASSWORD", "vietjobs_local_dev"),
    )
