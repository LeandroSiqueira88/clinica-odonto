from flask import Blueprint, render_template, request, redirect, flash, session, jsonify
from db import get_db_connection, is_postgres
from routes.utils import tipo_required, row_as_dict, rows_as_dicts
from datetime import datetime

consultas = Blueprint('consultas', __name__)

def p():
    return '%s' if is_postgres() else '?'

def obter_dia_semana(data):
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    dt = datetime.strptime(data, "%Y-%m-%d")
    return dias[dt.weekday()]

def fetch_all(cur, rows):
    return rows_as_dicts(rows, cur) if is_postgres() else rows

def fetch_one(cur, row):
    return row_as_dict(row, cur) if is_postgres() else row

@consultas.route('/consultas')
@tipo_required(['master', 'admin', 'atendente', 'dentista', 'operador'])
def agenda():
    dentista_id = request.args.get('dentista_id')
    especialidade = request.args.get('especialidade')
    conn = get_db_connection()
    cur = conn.cursor()
    query = '''SELECT c.*, p.nome as paciente, u.nome as dentista, u.especialidade
        FROM consultas c
        LEFT JOIN pacientes p ON p.id = c.paciente_id
        LEFT JOIN usuarios u ON u.id = c.dentista_id WHERE 1=1'''
    params = []
    if dentista_id:
        query += f' AND c.dentista_id = {p()}'; params.append(dentista_id)
    if especialidade:
        query += f' AND u.especialidade = {p()}'; params.append(especialidade)
    query += ' ORDER BY c.data, c.hora'
    cur.execute(query, params)
    lista = fetch_all(cur, cur.fetchall())
    cur.execute("SELECT * FROM usuarios WHERE tipo='dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('agenda.html', consultas=lista, dentistas=dents)

@consultas.route('/consultas/nova')
@tipo_required(['master', 'admin', 'atendente'])
def nova_consulta():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM pacientes')
    pacs = fetch_all(cur, cur.fetchall())
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('nova_consulta.html', pacientes=pacs, dentistas=dents)

@consultas.route('/consultas/salvar', methods=['POST'])
@tipo_required(['master', 'admin', 'atendente'])
def salvar_consulta():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        f'INSERT INTO consultas (paciente_id, dentista_id, data, hora, procedimento, status) VALUES ({p()},{p()},{p()},{p()},{p()},{p()})',
        (dados['paciente_id'], dados['dentista_id'], dados['data'], dados['hora'], dados['procedimento'], 'agendado')
    )
    conn.commit()
    conn.close()
    flash('Consulta agendada!')
    return redirect('/consultas')

@consultas.route('/escala')
@tipo_required(['master', 'admin'])
def escala():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT e.*, u.nome as dentista_nome FROM escala_dentistas e LEFT JOIN usuarios u ON u.id = e.dentista_id')
    lista = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('escala.html', escala=lista)

@consultas.route('/escala/nova')
@tipo_required(['master', 'admin'])
def nova_escala():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('nova_escala.html', dentistas=dents)

@consultas.route('/escala/salvar', methods=['POST'])
@tipo_required(['master', 'admin'])
def salvar_escala():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        f'INSERT INTO escala_dentistas (dentista_id, dia_semana, hora_inicio, hora_fim) VALUES ({p()},{p()},{p()},{p()})',
        (dados['dentista_id'], dados['dia_semana'], dados['hora_inicio'], dados['hora_fim'])
    )
    conn.commit()
    conn.close()
    flash('Escala cadastrada!')
    return redirect('/escala')

@consultas.route('/escala/editar/<int:id>')
@tipo_required(['master', 'admin'])
def editar_escala(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM escala_dentistas WHERE id = {p()}', (id,))
    esc = fetch_one(cur, cur.fetchone())
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('editar_escala.html', escala=esc, dentistas=dents)

@consultas.route('/escala/atualizar/<int:id>', methods=['POST'])
@tipo_required(['master', 'admin'])
def atualizar_escala(id):
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        f'UPDATE escala_dentistas SET dentista_id={p()}, dia_semana={p()}, hora_inicio={p()}, hora_fim={p()} WHERE id={p()}',
        (dados['dentista_id'], dados['dia_semana'], dados['hora_inicio'], dados['hora_fim'], id)
    )
    conn.commit()
    conn.close()
    flash('Escala atualizada!')
    return redirect('/escala')

@consultas.route('/minha_area/nova_consulta')
def nova_consulta_paciente():
    if 'usuario_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM pacientes WHERE usuario_id = {p()}', (session['usuario_id'],))
    pac = fetch_one(cur, cur.fetchone())
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('nova_consulta_paciente.html', paciente=pac, dentistas=dents)

@consultas.route('/minha_area/salvar_consulta', methods=['POST'])
def salvar_consulta_paciente():
    if 'usuario_id' not in session:
        return redirect('/login')
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM pacientes WHERE usuario_id = {p()}', (session['usuario_id'],))
    pac = fetch_one(cur, cur.fetchone())
    cur.execute(f'SELECT * FROM consultas WHERE dentista_id={p()} AND data={p()} AND hora={p()}',
        (dados['dentista_id'], dados['data'], dados['hora']))
    if cur.fetchone():
        conn.close(); return 'Horário já ocupado!'
    cur.execute(f'SELECT * FROM escala_dentistas WHERE dentista_id={p()} AND dia_semana={p()}',
        (dados['dentista_id'], obter_dia_semana(dados['data'])))
    esc = fetch_one(cur, cur.fetchone())
    if not esc:
        conn.close(); return 'Dentista não atende nesse dia!'
    if not (esc['hora_inicio'] <= dados['hora'] <= esc['hora_fim']):
        conn.close(); return 'Fora do horário do dentista!'
    cur.execute(
        f'INSERT INTO consultas (paciente_id, dentista_id, data, hora, procedimento, status) VALUES ({p()},{p()},{p()},{p()},{p()},{p()})',
        (pac['id'], dados['dentista_id'], dados['data'], dados['hora'], dados['procedimento'], 'agendado')
    )
    conn.commit()
    conn.close()
    return redirect('/minha_area')

@consultas.route('/consultas/horarios_disponiveis')
def horarios_disponiveis():
    dentista_id = request.args.get('dentista_id')
    data = request.args.get('data')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM escala_dentistas WHERE dentista_id={p()} AND dia_semana={p()}',
        (dentista_id, obter_dia_semana(data)))
    esc = fetch_one(cur, cur.fetchone())
    if not esc:
        conn.close(); return jsonify([])
    horarios = []
    inicio = int(esc['hora_inicio'].split(':')[0])
    fim = int(esc['hora_fim'].split(':')[0])
    for h in range(inicio, fim):
        horarios.append(f"{h:02d}:00")
        horarios.append(f"{h:02d}:30")
    cur.execute(f'SELECT hora FROM consultas WHERE dentista_id={p()} AND data={p()}', (dentista_id, data))
    ocupados = [r[0] for r in cur.fetchall()]
    conn.close()
    return jsonify([h for h in horarios if h not in ocupados])

@consultas.route('/consultas/verificar_dia')
def verificar_dia():
    dentista_id = request.args.get('dentista_id')
    data = request.args.get('data')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM escala_dentistas WHERE dentista_id={p()} AND dia_semana={p()}',
        (dentista_id, obter_dia_semana(data)))
    esc = cur.fetchone()
    conn.close()
    return jsonify({'valido': bool(esc)})

@consultas.route('/consultas/agenda_dentista')
def agenda_dentista():
    dentista_id = request.args.get('dentista_id')
    data = request.args.get('data')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM consultas WHERE dentista_id={p()} AND data={p()}', (dentista_id, data))
    lista = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('agenda_dentista.html', consultas=lista)

@consultas.route('/consultas/painel')
@tipo_required(['master', 'admin', 'atendente'])
def painel_agenda():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT c.*, p.nome as paciente, u.nome as dentista
        FROM consultas c LEFT JOIN pacientes p ON p.id = c.paciente_id
        LEFT JOIN usuarios u ON u.id = c.dentista_id ORDER BY data, hora''')
    lista = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('painel_agenda.html', consultas=lista)

@consultas.route('/consultas/eventos')
def eventos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT c.*, p.nome as paciente FROM consultas c LEFT JOIN pacientes p ON p.id = c.paciente_id')
    lista = fetch_all(cur, cur.fetchall())
    conn.close()
    return jsonify([{"id": c['id'], "title": f"{c['paciente']} - {c['procedimento']}", "start": f"{c['data']}T{c['hora']}"} for c in lista])

@consultas.route('/agenda_calendario')
@tipo_required(['master', 'admin', 'atendente', 'dentista', 'operador'])
def agenda_calendario():
    return render_template('agenda_calendario.html')

@consultas.route('/dashboard')
@tipo_required(['master', 'admin'])
def dashboard():
    return render_template('dashboard.html')

@consultas.route('/dashboard/dados')
@tipo_required(['master', 'admin'])
def dashboard_dados():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT data, COUNT(*) as total FROM consultas GROUP BY data ORDER BY data')
    dados = fetch_all(cur, cur.fetchall())
    conn.close()
    return jsonify({"labels": [d['data'] for d in dados], "valores": [d['total'] for d in dados]})

@consultas.route('/consultas/status/<int:id>/<status>')
@tipo_required(['master', 'admin', 'atendente'])
def atualizar_status(id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'UPDATE consultas SET status={p()} WHERE id={p()}', (status, id))
    conn.commit()
    conn.close()
    return redirect('/consultas')

@consultas.route('/consultas/detalhe/<int:id>')
@tipo_required(['master', 'admin', 'atendente', 'dentista', 'operador'])
def detalhe_consulta(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''SELECT c.*, p.nome as paciente, u.nome as dentista
        FROM consultas c LEFT JOIN pacientes p ON p.id = c.paciente_id
        LEFT JOIN usuarios u ON u.id = c.dentista_id WHERE c.id = {p()}''', (id,))
    c = fetch_one(cur, cur.fetchone())
    conn.close()
    if not c: return 'Consulta não encontrada'
    return render_template('consulta_detalhe.html', consulta=c)

@consultas.route('/consultas/mover', methods=['POST'])
@tipo_required(['master', 'admin', 'atendente'])
def mover_consulta():
    dados = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'UPDATE consultas SET data={p()}, hora={p()} WHERE id={p()}',
        (dados['data'], dados['hora'], dados['id']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
