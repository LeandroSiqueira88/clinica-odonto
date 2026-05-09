from flask import Blueprint, render_template, request, redirect, flash
import sqlite3
from routes.utils import tipo_required

dentistas = Blueprint('dentistas', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# 🦷 FORMULÁRIO
@dentistas.route('/dentistas')
@tipo_required(['master','admin'])
def form_dentista():
    return render_template('dentistas.html')


# 💾 SALVAR DENTISTA
@dentistas.route('/dentistas/salvar', methods=['POST'])
@tipo_required(['master','admin'])
def salvar_dentista():
    dados = request.form

    conn = get_db_connection()

    conn.execute('''
        INSERT INTO usuarios (nome, email, senha, tipo, especialidade, cro)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        dados['nome'],
        dados['email'],
        dados['senha'],
        'dentista',
        dados['especialidade'],
        dados['cro']
    ))

    conn.commit()
    conn.close()

    flash('Dentista cadastrado com sucesso!')
    return redirect('/usuarios/lista')