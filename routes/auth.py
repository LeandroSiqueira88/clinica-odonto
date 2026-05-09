from flask import Blueprint, render_template, request, redirect, session, url_for
from db import get_db_connection, is_postgres
from routes.utils import tipo_required, row_as_dict, rows_as_dicts

auth = Blueprint('auth', __name__)

def p():
    return '%s' if is_postgres() else '?'

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = request.form['senha'].strip()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM usuarios WHERE email = {p()}', (email,))
        row = cur.fetchone()
        user = row_as_dict(row, cur) if is_postgres() else row
        conn.close()
        if user:
            if user['senha'] == senha:
                session['usuario_id'] = user['id']
                session['usuario_nome'] = user['nome']
                session['usuario_tipo'] = user['tipo']
                return redirect(url_for('main.home'))
            return render_template('login.html', erro='Senha incorreta')
        return render_template('login.html', erro='Usuário não encontrado')
    return render_template('login.html', erro=None)

@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@auth.route('/usuarios')
@tipo_required(['master', 'admin'])
def usuarios():
    return render_template('usuarios.html')

@auth.route('/usuarios/salvar', methods=['POST'])
@tipo_required(['master', 'admin'])
def salvar_usuario():
    nome = request.form['nome']
    email = request.form['email'].strip()
    senha = request.form['senha'].strip()
    tipo = request.form['tipo']
    especialidade = request.form.get('especialidade', '')
    cro = request.form.get('cro', '')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        f'INSERT INTO usuarios (nome, email, senha, tipo, especialidade, cro) VALUES ({p()},{p()},{p()},{p()},{p()},{p()})',
        (nome, email, senha, tipo, especialidade, cro)
    )
    conn.commit()
    conn.close()
    return redirect('/usuarios/lista')

@auth.route('/usuarios/lista')
@tipo_required(['master', 'admin'])
def lista_usuarios():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE tipo != 'cliente'")
    rows = cur.fetchall()
    usuarios = rows_as_dicts(rows, cur) if is_postgres() else rows
    conn.close()
    return render_template('lista_usuarios.html', usuarios=usuarios, busca='')

@auth.route('/usuarios/editar/<int:id>')
@tipo_required(['master', 'admin'])
def editar_usuario(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM usuarios WHERE id = {p()}', (id,))
    row = cur.fetchone()
    usuario = row_as_dict(row, cur) if is_postgres() else row
    conn.close()
    return render_template('editar_usuario.html', usuario=usuario)

@auth.route('/usuarios/atualizar/<int:id>', methods=['POST'])
@tipo_required(['master', 'admin'])
def atualizar_usuario(id):
    nome = request.form['nome']
    email = request.form['email']
    tipo = request.form['tipo']
    especialidade = request.form.get('especialidade', '')
    cro = request.form.get('cro', '')
    senha = request.form.get('senha', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()
    if senha:
        cur.execute(
            f'UPDATE usuarios SET nome={p()}, email={p()}, senha={p()}, tipo={p()}, especialidade={p()}, cro={p()} WHERE id={p()}',
            (nome, email, senha, tipo, especialidade, cro, id)
        )
    else:
        cur.execute(
            f'UPDATE usuarios SET nome={p()}, email={p()}, tipo={p()}, especialidade={p()}, cro={p()} WHERE id={p()}',
            (nome, email, tipo, especialidade, cro, id)
        )
    conn.commit()
    conn.close()
    return redirect('/usuarios/lista')

@auth.route('/usuarios/excluir/<int:id>')
@tipo_required(['master', 'admin'])
def excluir_usuario(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'DELETE FROM usuarios WHERE id = {p()}', (id,))
    conn.commit()
    conn.close()
    return redirect('/usuarios/lista')
