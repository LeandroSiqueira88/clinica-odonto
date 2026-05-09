from flask import Blueprint, render_template, request, redirect, session, url_for
import sqlite3
from routes.utils import tipo_required

auth = Blueprint('auth', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = request.form['senha'].strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE email = ?', (email,)
        ).fetchone()
        conn.close()

        if user:
            if user['senha'] == senha:
                session['usuario_id'] = user['id']
                session['usuario_nome'] = user['nome']
                session['usuario_tipo'] = user['tipo']
                return redirect(url_for('main.home'))
            else:
                return render_template('login.html', erro="Senha incorreta")

        return render_template('login.html', erro="Usuário não encontrado")

    return render_template('login.html', erro=None)


@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@auth.route('/usuarios')
@tipo_required(['master'])
def usuarios():
    return render_template('usuarios.html')


@auth.route('/usuarios/salvar', methods=['POST'])
@tipo_required(['master'])
def salvar_usuario():
    nome = request.form['nome']
    email = request.form['email'].strip()
    senha = request.form['senha'].strip()
    tipo = request.form['tipo']
    especialidade = request.form.get('especialidade', '')
    cro = request.form.get('cro', '')

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO usuarios (nome, email, senha, tipo, especialidade, cro)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, email, senha, tipo, especialidade, cro))
    conn.commit()
    conn.close()

    return redirect('/usuarios/lista')


@auth.route('/usuarios/lista')
@tipo_required(['master'])
def lista_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute(
        "SELECT * FROM usuarios WHERE tipo != 'cliente'"
    ).fetchall()
    conn.close()
    return render_template('lista_usuarios.html', usuarios=usuarios, busca='')


@auth.route('/usuarios/editar/<int:id>')
@tipo_required(['master'])
def editar_usuario(id):
    conn = get_db_connection()
    usuario = conn.execute("SELECT * FROM usuarios WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('editar_usuario.html', usuario=usuario)


@auth.route('/usuarios/atualizar/<int:id>', methods=['POST'])
@tipo_required(['master'])
def atualizar_usuario(id):
    nome = request.form['nome']
    email = request.form['email']
    tipo = request.form['tipo']
    especialidade = request.form.get('especialidade', '')
    cro = request.form.get('cro', '')

    conn = get_db_connection()
    conn.execute('''
        UPDATE usuarios 
        SET nome=?, email=?, tipo=?, especialidade=?, cro=?
        WHERE id=?
    ''', (nome, email, tipo, especialidade, cro, id))
    conn.commit()
    conn.close()

    return redirect('/usuarios/lista')


@auth.route('/usuarios/excluir/<int:id>')
@tipo_required(['master'])
def excluir_usuario(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/usuarios/lista')
