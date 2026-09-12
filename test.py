import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if "sslmode=" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{separator}sslmode=require"

conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True
)

with conn.cursor() as cur:

    cur.execute("SELECT COUNT(*) FROM checkpoints;")
    print("CHECKPOINTS:", cur.fetchone())

    cur.execute("SELECT COUNT(*) FROM checkpoint_blobs;")
    print("BLOBS:", cur.fetchone())

    cur.execute("SELECT COUNT(*) FROM checkpoint_writes;")
    print("WRITES:", cur.fetchone())

    cur.execute("""
        SELECT
            thread_id,
            checkpoint_ns,
            checkpoint_id
        FROM checkpoints
        ORDER BY checkpoint_id DESC
        LIMIT 10;
    """)

    print("\nCHECKPOINT DATA:")
    for row in cur.fetchall():
        print(row)

conn.close()