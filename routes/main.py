from flask import Blueprint, render_template, session, redirect
import sqlite3

main = Blueprint('main', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# 🏠 HOME
@main.route('/')
def home():
    if 'usuario_id' not in session:
        return redirect('/login')

    # 👤 PACIENTE VAI PARA SUA ÁREA
    if session['usuario_tipo'] == 'cliente':
        return redirect('/minha_area')

    return render_template('index.html')


# 👤 ÁREA DO PACIENTE
@main.route('/minha_area')
def minha_area():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    consultas = conn.execute('''
        SELECT c.*, u.nome as dentista_nome
        FROM consultas c
        LEFT JOIN usuarios u ON u.id = c.dentista_id
        LEFT JOIN pacientes p ON p.id = c.paciente_id
        WHERE p.usuario_id = ?
        ORDER BY c.data, c.hora
    ''', (session['usuario_id'],)).fetchall()

    conn.close()

    return render_template('minha_area.html', consultas=consultas)