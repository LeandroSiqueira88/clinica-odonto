from flask import session, redirect

def login_required():
    if 'usuario_id' not in session:
        return redirect('/login')

def tipo_required(tipos_permitidos):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'usuario_tipo' not in session:
                return redirect('/login')

            if session['usuario_tipo'] not in tipos_permitidos:
                return "<h1>Acesso negado</h1>"

            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator