from flask import Blueprint, render_template, session, redirect
from db import get_db_connection, is_postgres
from routes.utils import rows_as_dicts

main = Blueprint('main', __name__)

def p():
    return '%s' if is_postgres() else '?'

@main.route('/')
def home():
    if 'usuario_id' not in session:
        return redirect('/login')
    if session['usuario_tipo'] == 'cliente':
        return redirect('/minha_area')
    return render_template('index.html')

@main.route('/minha_area')
def minha_area():
    if 'usuario_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''
        SELECT c.*, u.nome as dentista_nome
        FROM consultas c
        LEFT JOIN usuarios u ON u.id = c.dentista_id
        LEFT JOIN pacientes p ON p.id = c.paciente_id
        WHERE p.usuario_id = {p()}
        ORDER BY c.data, c.hora
    ''', (session['usuario_id'],))
    rows = cur.fetchall()
    consultas = rows_as_dicts(rows, cur) if is_postgres() else rows
    conn.close()
    return render_template('minha_area.html', consultas=consultas)
