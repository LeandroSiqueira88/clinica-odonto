from flask import session, redirect
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def tipo_required(tipos_permitidos):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'usuario_tipo' not in session:
                return redirect('/login')
            if session['usuario_tipo'] not in tipos_permitidos:
                return "<h1>Acesso negado</h1>"
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rows_as_dicts(rows, cursor):
    """Converte rows do psycopg2 para lista de dicts acessíveis por nome"""
    if not rows:
        return []
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in rows]

def row_as_dict(row, cursor):
    """Converte uma row do psycopg2 para dict"""
    if not row:
        return None
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))
