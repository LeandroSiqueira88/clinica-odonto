from flask import Blueprint, render_template, request, redirect, flash
import sqlite3
from routes.utils import tipo_required

pacientes = Blueprint('pacientes', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# 📄 CADASTRO (PÚBLICO)
@pacientes.route('/cadastro')
def cadastro():
    return render_template('cadastro_paciente.html', paciente=None)


# 💾 SALVAR PACIENTE + USUÁRIO
@pacientes.route('/pacientes/salvar', methods=['POST'])
def salvar_paciente():
    dados = request.form

    conn = get_db_connection()
    cursor = conn.cursor()

    email_login = dados.get('email_login', '').strip()
    senha = dados.get('senha', '').strip()

    usuario_id = None

    # 🔐 cria usuário (cliente)
    if email_login and senha:
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, tipo)
            VALUES (?, ?, ?, ?)
        ''', (
            dados.get('nome'),
            email_login,
            senha,
            'cliente'
        ))

        usuario_id = cursor.lastrowid

    # 👤 cria paciente vinculado ao usuário
    cursor.execute('''
        INSERT INTO pacientes (
            usuario_id, nome, data_nascimento, sexo, cpf, telefone, email,
            cep, logradouro, bairro, cidade, estado,
            numero, complemento, responsavel_nome
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        usuario_id,
        dados.get('nome'),
        dados.get('data_nascimento'),
        dados.get('sexo'),
        dados.get('cpf'),
        dados.get('telefone'),
        dados.get('email'),
        dados.get('cep'),
        dados.get('logradouro'),
        dados.get('bairro'),
        dados.get('cidade'),
        dados.get('estado'),
        dados.get('numero'),
        dados.get('complemento'),
        dados.get('responsavel_nome')
    ))

    conn.commit()
    conn.close()

    flash('Paciente cadastrado com sucesso!')
    return redirect('/login')


# 📋 LISTA
@pacientes.route('/pacientes/lista')
@tipo_required(['master', 'admin', 'atendente', 'dentista'])
def lista_pacientes():
    conn = get_db_connection()

    pacientes_lista = conn.execute(
        "SELECT * FROM pacientes ORDER BY nome"
    ).fetchall()

    conn.close()

    return render_template('lista_pacientes.html', pacientes=pacientes_lista)


# ✏️ EDITAR
@pacientes.route('/pacientes/editar/<int:id>')
@tipo_required(['master', 'admin'])
def editar_paciente(id):
    conn = get_db_connection()

    paciente = conn.execute(
        "SELECT * FROM pacientes WHERE id = ?", (id,)
    ).fetchone()

    conn.close()

    return render_template('cadastro_paciente.html', paciente=paciente)


# 💾 ATUALIZAR
@pacientes.route('/pacientes/atualizar/<int:id>', methods=['POST'])
@tipo_required(['master', 'admin'])
def atualizar_paciente(id):
    dados = request.form

    conn = get_db_connection()

    conn.execute('''
        UPDATE pacientes
        SET nome=?, data_nascimento=?, sexo=?, cpf=?, telefone=?, email=?,
            cep=?, logradouro=?, bairro=?, cidade=?, estado=?,
            numero=?, complemento=?, responsavel_nome=?
        WHERE id=?
    ''', (
        dados.get('nome'),
        dados.get('data_nascimento'),
        dados.get('sexo'),
        dados.get('cpf'),
        dados.get('telefone'),
        dados.get('email'),
        dados.get('cep'),
        dados.get('logradouro'),
        dados.get('bairro'),
        dados.get('cidade'),
        dados.get('estado'),
        dados.get('numero'),
        dados.get('complemento'),
        dados.get('responsavel_nome'),
        id
    ))

    conn.commit()
    conn.close()

    flash('Paciente atualizado com sucesso!')
    return redirect('/pacientes/lista')

@pacientes.route('/prontuario/<int:id>')
def prontuario(id):
    conn = get_db_connection()

    registros = conn.execute(
        "SELECT * FROM prontuario WHERE paciente_id = ?",
        (id,)
    ).fetchall()

    conn.close()

    return render_template('prontuario.html', registros=registros, paciente_id=id)


@pacientes.route('/prontuario/salvar', methods=['POST'])
def salvar_prontuario():
    dados = request.form

    conn = get_db_connection()

    conn.execute('''
        INSERT INTO prontuario (paciente_id, historico, diagnostico, tratamento, data)
        VALUES (?, ?, ?, ?, date('now'))
    ''', (
        dados['paciente_id'],
        dados['historico'],
        dados['diagnostico'],
        dados['tratamento']
    ))

    conn.commit()
    conn.close()

    return redirect(f"/prontuario/{dados['paciente_id']}")

@pacientes.route('/pacientes/anamnese/<int:id>')
def anamnese(id):
    conn = get_db_connection()

    anamnese = conn.execute(
        "SELECT * FROM anamneses WHERE paciente_id = ?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template('anamnese.html', anamnese=anamnese, paciente_id=id)

@pacientes.route('/pacientes/anamnese/salvar', methods=['POST'])
def salvar_anamnese():
    dados = request.form

    conn = get_db_connection()

    existente = conn.execute(
        "SELECT * FROM anamneses WHERE paciente_id = ?",
        (dados['paciente_id'],)
    ).fetchone()

    if existente:
        conn.execute('''
            UPDATE anamneses
            SET alergias=?, medicamentos=?, doencas=?, observacoes=?
            WHERE paciente_id=?
        ''', (
            dados['alergias'],
            dados['medicamentos'],
            dados['doencas'],
            dados['observacoes'],
            dados['paciente_id']
        ))
    else:
        conn.execute('''
            INSERT INTO anamneses (paciente_id, alergias, medicamentos, doencas, observacoes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            dados['paciente_id'],
            dados['alergias'],
            dados['medicamentos'],
            dados['doencas'],
            dados['observacoes']
        ))

    conn.commit()
    conn.close()

    return redirect('/pacientes/lista')