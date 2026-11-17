import os
import time
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "database": os.getenv("DB_NAME", "notesdb"),
    "user": os.getenv("DB_USER", "notesuser"),
    "password": os.getenv("DB_PASSWORD"),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def initialize_database():
    for attempt in range(10):
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL
                )
            """)

            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully")
            return

        except psycopg2.OperationalError:
            print(f"Database not ready. Retry {attempt + 1}/10")
            time.sleep(3)

    raise RuntimeError("Could not connect to the database")


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json(silent=True) or {}
    content = data.get("content")

    if not content:
        return jsonify({"error": "content is required"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO notes (content) VALUES (%s) RETURNING id",
        (content,)
    )

    note_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"id": note_id, "content": content}), 201


@app.route("/notes")
def get_notes():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, content FROM notes ORDER BY id")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify([
        {"id": row[0], "content": row[1]}
        for row in rows
    ])


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)