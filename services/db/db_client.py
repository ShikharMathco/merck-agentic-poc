# db/db_client.py
import psycopg2
import os

# -----------------------------
# CONFIG
# -----------------------------
POSTGRES_CONFIG = {
    "dbname": os.getenv("PG_DBNAME", "dummy_poc"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
}

# -----------------------------
# INIT CONNECTION
# -----------------------------
def get_connection():
    return psycopg2.connect(**POSTGRES_CONFIG)

# -----------------------------
# RUN SQL QUERY
# -----------------------------
def run_sql(query):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query)

    try:
        results = cursor.fetchall()
    except psycopg2.ProgrammingError:
        results = []  # no rows returned (DDL commands etc.)

    conn.commit()
    conn.close()
    return results

# -----------------------------
# TEST (optional)
# -----------------------------
if __name__ == "__main__":
    print(run_sql("SELECT NOW();"))
