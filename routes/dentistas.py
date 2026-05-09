from flask import Blueprint, render_template, request, redirect, flash
from db import get_db_connection, is_postgres
from routes.utils import tipo_required

dentistas = Blueprint('dentistas', __name__)

def p():
    return '%s' if is_postgres() else '?'

@dentistas.route('/dentistas')
@tipo_required(['master', 'admin'])
def form_dentista():
    return render_template('dentistas.html')

@dentistas.route('/dentistas/salvar', methods=['POST'])
@tipo_required(['master', 'admin'])
def salvar_dentista():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        f'INSERT INTO usuarios (nome, email, senha, tipo, especialidade, cro) VALUES ({p()},{p()},{p()},{p()},{p()},{p()})',
        (dados['nome'], dados['email'], dados['senha'], 'dentista', dados['especialidade'], dados['cro'])
    )
    conn.commit()
    conn.close()
    flash('Dentista cadastrado com sucesso!')
    return redirect('/usuarios/lista')
