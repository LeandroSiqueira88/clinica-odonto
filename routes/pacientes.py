from flask import Blueprint, render_template, request, redirect, flash, session
from db import get_db_connection, is_postgres
from routes.utils import tipo_required, row_as_dict, rows_as_dicts

def fetch_one(cur, row):
    from db import is_postgres
    return row_as_dict(row, cur) if is_postgres() else row

def fetch_all(cur, rows):
    from routes.utils import rows_as_dicts
    from db import is_postgres
    return rows_as_dicts(rows, cur) if is_postgres() else rows

pacientes = Blueprint('pacientes', __name__)

def p():
    return '%s' if is_postgres() else '?'

@pacientes.route('/cadastro')
def cadastro():
    return render_template('cadastro_paciente.html', paciente=None)

@pacientes.route('/pacientes/salvar', methods=['POST'])
def salvar_paciente():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    email_login = dados.get('email_login', '').strip()
    senha = dados.get('senha', '').strip()
    usuario_id = None

    # Verificar se email já existe antes de tentar inserir
    if email_login:
        cur.execute(f'SELECT id FROM usuarios WHERE email = {p()}', (email_login,))
        if cur.fetchone():
            conn.close()
            flash('Este email de acesso já está cadastrado. Use outro email ou deixe em branco.')
            return redirect('/cadastro')

    if email_login and senha:
        try:
            cur.execute(
                f'INSERT INTO usuarios (nome, email, senha, tipo) VALUES ({p()},{p()},{p()},{p()})',
                (dados.get('nome'), email_login, senha, 'cliente')
            )
            if is_postgres():
                cur.execute('SELECT lastval()')
                usuario_id = cur.fetchone()[0]
            else:
                usuario_id = cur.lastrowid
        except Exception:
            conn.close()
            flash('Este email de acesso já está cadastrado. Use outro email ou deixe em branco.')
            return redirect('/cadastro')

    cur.execute(f'''
        INSERT INTO pacientes (usuario_id, nome, data_nascimento, sexo, cpf, telefone, email,
            cep, logradouro, bairro, cidade, estado, numero, complemento, responsavel_nome)
        VALUES ({p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()})
    ''', (
        usuario_id, dados.get('nome'), dados.get('data_nascimento'), dados.get('sexo'),
        dados.get('cpf'), dados.get('telefone'), dados.get('email'), dados.get('cep'),
        dados.get('logradouro'), dados.get('bairro'), dados.get('cidade'), dados.get('estado'),
        dados.get('numero'), dados.get('complemento'), dados.get('responsavel_nome')
    ))
    conn.commit()
    conn.close()
    flash('Paciente cadastrado com sucesso!')
    return redirect('/pacientes/lista')

@pacientes.route('/pacientes/lista')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def lista_pacientes():
    busca = request.args.get('busca', '')
    conn = get_db_connection()
    cur = conn.cursor()
    if busca:
        cur.execute(f"SELECT * FROM pacientes WHERE nome LIKE {p()} ORDER BY nome", (f'%{busca}%',))
    else:
        cur.execute("SELECT * FROM pacientes ORDER BY nome")
    rows = cur.fetchall()
    lista = rows_as_dicts(rows, cur) if is_postgres() else rows
    conn.close()
    return render_template('lista_pacientes.html', pacientes=lista, busca=busca)

@pacientes.route('/pacientes/editar/<int:id>')
@tipo_required(['master', 'admin'])
def editar_paciente(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM pacientes WHERE id = {p()}', (id,))
    row = cur.fetchone()
    paciente = row_as_dict(row, cur) if is_postgres() else row
    conn.close()
    return render_template('cadastro_paciente.html', paciente=paciente)

@pacientes.route('/pacientes/atualizar/<int:id>', methods=['POST'])
@tipo_required(['master', 'admin'])
def atualizar_paciente(id):
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''
        UPDATE pacientes SET nome={p()}, data_nascimento={p()}, sexo={p()}, cpf={p()},
        telefone={p()}, email={p()}, cep={p()}, logradouro={p()}, bairro={p()},
        cidade={p()}, estado={p()}, numero={p()}, complemento={p()}, responsavel_nome={p()}
        WHERE id={p()}
    ''', (
        dados.get('nome'), dados.get('data_nascimento'), dados.get('sexo'), dados.get('cpf'),
        dados.get('telefone'), dados.get('email'), dados.get('cep'), dados.get('logradouro'),
        dados.get('bairro'), dados.get('cidade'), dados.get('estado'), dados.get('numero'),
        dados.get('complemento'), dados.get('responsavel_nome'), id
    ))

    # Atualizar email e senha do usuário vinculado
    email_login = dados.get('email_login', '').strip()
    senha = dados.get('senha', '').strip()
    if email_login or senha:
        cur.execute(f'SELECT usuario_id FROM pacientes WHERE id = {p()}', (id,))
        row = cur.fetchone()
        usuario_id = row[0] if row else None
        if usuario_id:
            if email_login and senha:
                cur.execute(f'UPDATE usuarios SET email={p()}, senha={p()} WHERE id={p()}',
                    (email_login, senha, usuario_id))
            elif email_login:
                cur.execute(f'UPDATE usuarios SET email={p()} WHERE id={p()}',
                    (email_login, usuario_id))
            elif senha:
                cur.execute(f'UPDATE usuarios SET senha={p()} WHERE id={p()}',
                    (senha, usuario_id))

    conn.commit()
    conn.close()
    flash('Paciente atualizado!')
    return redirect('/pacientes/lista')

@pacientes.route('/pacientes/excluir/<int:id>')
@tipo_required(['master', 'admin'])
def excluir_paciente(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'DELETE FROM pacientes WHERE id = {p()}', (id,))
    conn.commit()
    conn.close()
    return redirect('/pacientes/lista')

@pacientes.route('/prontuario/<int:id>')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def prontuario(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM prontuario WHERE paciente_id = {p()}', (id,))
    rows = cur.fetchall()
    registros = rows_as_dicts(rows, cur) if is_postgres() else rows
    conn.close()
    return render_template('prontuario.html', registros=registros, paciente_id=id)

@pacientes.route('/prontuario/salvar', methods=['POST'])
@tipo_required(['master', 'admin', 'dentista'])
def salvar_prontuario():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    data_hoje = 'CURRENT_DATE' if is_postgres() else "date('now')"
    cur.execute(
        f'INSERT INTO prontuario (paciente_id, historico, diagnostico, tratamento, data) VALUES ({p()},{p()},{p()},{p()},{data_hoje})',
        (dados['paciente_id'], dados['historico'], dados['diagnostico'], dados['tratamento'])
    )
    conn.commit()
    conn.close()
    return redirect(f"/prontuario/{dados['paciente_id']}")

@pacientes.route('/pacientes/anamnese/<int:id>')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def anamnese(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM anamneses WHERE paciente_id = {p()}', (id,))
    row = cur.fetchone()
    anam = row_as_dict(row, cur) if is_postgres() else row
    conn.close()
    return render_template('anamnese.html', anamnese=anam, paciente_id=id)

@pacientes.route('/pacientes/anamnese/salvar', methods=['POST'])
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def salvar_anamnese():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT id FROM anamneses WHERE paciente_id = {p()}', (dados['paciente_id'],))
    existente = cur.fetchone()
    if existente:
        cur.execute(f'''
            UPDATE anamneses SET alergias={p()}, medicamentos={p()}, doencas={p()}, observacoes={p()}
            WHERE paciente_id={p()}
        ''', (dados['alergias'], dados['medicamentos'], dados['doencas'], dados['observacoes'], dados['paciente_id']))
    else:
        cur.execute(f'''
            INSERT INTO anamneses (paciente_id, alergias, medicamentos, doencas, observacoes)
            VALUES ({p()},{p()},{p()},{p()},{p()})
        ''', (dados['paciente_id'], dados['alergias'], dados['medicamentos'], dados['doencas'], dados['observacoes']))
    conn.commit()
    conn.close()
    return redirect('/pacientes/lista')


@pacientes.route('/pacientes/ficha/<int:id>')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def ficha_paciente(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM pacientes WHERE id = {p()}', (id,))
    pac = fetch_one(cur, cur.fetchone())

    cur.execute(f'''SELECT c.*, u.nome as dentista_nome FROM consultas c
        LEFT JOIN usuarios u ON u.id = c.dentista_id
        WHERE c.paciente_id = {p()} ORDER BY c.data DESC, c.hora DESC''', (id,))
    consultas = fetch_all(cur, cur.fetchall())

    cur.execute(f'''SELECT a.*, u.nome as dentista_nome FROM atendimentos a
        LEFT JOIN usuarios u ON u.id = a.dentista_id
        WHERE a.paciente_id = {p()} ORDER BY a.data DESC''', (id,))
    atendimentos = fetch_all(cur, cur.fetchall())

    conn.close()
    return render_template('ficha_paciente.html', paciente=pac, consultas=consultas, atendimentos=atendimentos)

@pacientes.route('/atendimento/novo/<int:id>')
@tipo_required(['master', 'admin', 'dentista'])
def novo_atendimento(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM pacientes WHERE id = {p()}', (id,))
    pac = fetch_one(cur, cur.fetchone())
    conn.close()
    return render_template('novo_atendimento.html', paciente=pac)

@pacientes.route('/atendimento/salvar', methods=['POST'])
@tipo_required(['master', 'admin', 'dentista'])
def salvar_atendimento():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''INSERT INTO atendimentos
        (paciente_id, dentista_id, data, queixa, diagnostico, tratamento, prescricao, observacoes, retorno)
        VALUES ({p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()})''',
        (dados['paciente_id'], session.get('usuario_id'), dados['data'],
         dados.get('queixa'), dados.get('diagnostico'), dados.get('tratamento'),
         dados.get('prescricao'), dados.get('observacoes'), dados.get('retorno') or None))
    conn.commit()
    conn.close()
    flash('Atendimento registrado com sucesso!')
    return redirect(f"/pacientes/ficha/{dados['paciente_id']}")