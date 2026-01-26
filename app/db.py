# app/db.py
import sqlite3
import time
from app.config import DB_PATH

def db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn

def now_ts() -> float:
    return time.time()

def db_init():
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        phone TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        nid TEXT NOT NULL,
        password TEXT NOT NULL,
        created_ts REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS referees(
        phone TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        nid TEXT NOT NULL,
        field TEXT NOT NULL,
        password TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_ts REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics(
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        field TEXT NOT NULL,
        description TEXT NOT NULL,
        file_name TEXT,
        file_bytes BLOB,
        created_ts REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS research(
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        field TEXT NOT NULL,
        summary TEXT NOT NULL,
        file_name TEXT,
        file_bytes BLOB,
        created_ts REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents(
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_bytes BLOB NOT NULL,
        created_ts REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS submissions(
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        sender_phone TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        sender_nid TEXT NOT NULL,
        suggested_topic_id TEXT,
        field TEXT NOT NULL,
        content_type TEXT NOT NULL,
        file_name TEXT,
        file_mime TEXT,
        file_bytes BLOB,
        status TEXT NOT NULL,
        likes INTEGER NOT NULL DEFAULT 0,
        views INTEGER NOT NULL DEFAULT 0,
        knowledge_code TEXT,
        created_ts REAL NOT NULL,
        FOREIGN KEY(sender_phone) REFERENCES users(phone) ON DELETE NO ACTION
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS submission_assignments(
        id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL,
        referee_phone TEXT NOT NULL,
        referee_name TEXT NOT NULL,
        referee_field TEXT NOT NULL,
        decision TEXT NOT NULL,
        feedback TEXT NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        suggested_knowledge_code TEXT,
        reviewed_ts REAL,
        created_ts REAL NOT NULL,
        FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS submission_likes(
        submission_id TEXT NOT NULL,
        user_phone TEXT NOT NULL,
        created_ts REAL NOT NULL,
        PRIMARY KEY(submission_id, user_phone),
        FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS submission_comments(
        id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL,
        user_name TEXT NOT NULL,
        text TEXT NOT NULL,
        created_ts REAL NOT NULL,
        FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS forum_posts(
        id TEXT PRIMARY KEY,
        sender_phone TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        sender_role TEXT NOT NULL,
        text TEXT NOT NULL,
        status TEXT NOT NULL,
        created_ts REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS forum_replies(
        id TEXT PRIMARY KEY,
        post_id TEXT NOT NULL,
        referee_phone TEXT NOT NULL,
        referee_name TEXT NOT NULL,
        text TEXT NOT NULL,
        created_ts REAL NOT NULL,
        FOREIGN KEY(post_id) REFERENCES forum_posts(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

