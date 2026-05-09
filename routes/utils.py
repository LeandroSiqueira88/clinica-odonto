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
