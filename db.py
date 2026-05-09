import os
import sqlite3

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn

def is_postgres():
    return bool(DATABASE_URL)

def placeholder():
    """Retorna %s para postgres ou ? para sqlite"""
    return '%s' if is_postgres() else '?'
