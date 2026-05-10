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
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def agenda():
    dentista_id = request.args.get('dentista_id')
    especialidade = request.args.get('especialidade')
    paciente_nome = request.args.get('paciente', '')
    status = request.args.get('status', '')
    data_filtro = request.args.get('data', '')
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
    if paciente_nome:
        query += f' AND p.nome ILIKE {p()}' if is_postgres() else f' AND p.nome LIKE {p()}'
        params.append(f'%{paciente_nome}%')
    if status:
        query += f' AND c.status = {p()}'; params.append(status)
    if data_filtro:
        query += f' AND c.data = {p()}'; params.append(data_filtro)
    query += ' ORDER BY c.data, c.hora'
    cur.execute(query, params)
    lista = fetch_all(cur, cur.fetchall())
    cur.execute("SELECT * FROM usuarios WHERE tipo='dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('agenda.html', consultas=lista, dentistas=dents)

@consultas.route('/consultas/nova')
@tipo_required(['master', 'admin', 'operador', 'atendente'])
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
@tipo_required(['master', 'admin', 'operador', 'atendente'])
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
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def escala():
    tipo = session.get('usuario_tipo')
    dentista_id = request.args.get('dentista_id')
    dia_semana  = request.args.get('dia_semana')

    conn = get_db_connection()
    cur = conn.cursor()
    query = 'SELECT e.*, u.nome as dentista_nome FROM escala_dentistas e LEFT JOIN usuarios u ON u.id = e.dentista_id WHERE 1=1'
    params = []

    # Dentista só vê a própria escala
    if tipo == 'dentista':
        query += f' AND e.dentista_id = {p()}'
        params.append(session.get('usuario_id'))
    elif dentista_id:
        query += f' AND e.dentista_id = {p()}'; params.append(dentista_id)

    if dia_semana:
        query += f' AND e.dia_semana = {p()}'; params.append(dia_semana)
    query += ' ORDER BY u.nome, e.dia_semana'
    cur.execute(query, params)
    lista = fetch_all(cur, cur.fetchall())
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista' ORDER BY nome")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    # Atendente e dentista só podem visualizar (pode_editar=False)
    pode_editar = tipo in ['master', 'admin', 'operador']
    return render_template('escala.html', escala=lista, dentistas=dents, pode_editar=pode_editar)

@consultas.route('/escala/nova')
@tipo_required(['master', 'admin', 'operador'])
def nova_escala():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('nova_escala.html', dentistas=dents)

@consultas.route('/escala/salvar', methods=['POST'])
@tipo_required(['master', 'admin', 'operador'])
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
@tipo_required(['master', 'admin', 'operador'])
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
@tipo_required(['master', 'admin', 'operador'])
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
    cur.execute("SELECT * FROM pacientes ORDER BY nome")
    todos_pacientes = fetch_all(cur, cur.fetchall())
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista'")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('nova_consulta_paciente.html', paciente=pac, pacientes=todos_pacientes, dentistas=dents)

@consultas.route('/minha_area/salvar_consulta', methods=['POST'])
def salvar_consulta_paciente():
    if 'usuario_id' not in session:
        return redirect('/login')
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    # Usa paciente_id do form se informado, senão pega pelo usuário logado
    paciente_id_form = dados.get('paciente_id')
    if paciente_id_form:
        cur.execute(f'SELECT * FROM pacientes WHERE id = {p()}', (paciente_id_form,))
    else:
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
@tipo_required(['master', 'admin', 'operador', 'atendente'])
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
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def agenda_calendario():
    return render_template('agenda_calendario.html')

@consultas.route('/dashboard')
@consultas.route('/dashboard/')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def dashboard():
    return render_template('dashboard.html')

@consultas.route('/dashboard/dados')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def dashboard_dados():
    # Dentista só vê seus próprios dados
    filtro_dentista_id = None
    if session.get('usuario_tipo') == 'dentista':
        filtro_dentista_id = session.get('usuario_id')

    conn = get_db_connection()
    cur = conn.cursor()

    if is_postgres():
        hoje_expr     = "CURRENT_DATE"
        semana_expr   = "CURRENT_DATE - INTERVAL '7 days'"
        quinzena_expr = "CURRENT_DATE - INTERVAL '15 days'"
        mes_expr      = "DATE_TRUNC('month', CURRENT_DATE)"
        ano_expr      = "DATE_TRUNC('year', CURRENT_DATE)"
        cast_d        = "c.data::date"
    else:
        hoje_expr     = "date('now')"
        semana_expr   = "date('now','-7 days')"
        quinzena_expr = "date('now','-15 days')"
        mes_expr      = "date('now','start of month')"
        ano_expr      = "date('now','start of year')"
        cast_d        = "c.data"

    def count_total(where_clause):
        q = f"SELECT COUNT(*) FROM consultas c WHERE status='atendido' AND {where_clause}"
        params_q = []
        if filtro_dentista_id:
            q += f" AND c.dentista_id = {p()}"
            params_q.append(filtro_dentista_id)
        cur.execute(q, params_q)
        return cur.fetchone()[0]

    totais = {
        'hoje':      count_total(f"{cast_d} = {hoje_expr}"),
        'semana':    count_total(f"{cast_d} >= {semana_expr}"),
        'quinzena':  count_total(f"{cast_d} >= {quinzena_expr}"),
        'mes':       count_total(f"{cast_d} >= {mes_expr}"),
        'ano':       count_total(f"{cast_d} >= {ano_expr}"),
    }

    if is_postgres():
        cur.execute("SELECT c.data::text as data, COUNT(*) as total FROM consultas c WHERE status='atendido' AND c.data::date >= CURRENT_DATE - INTERVAL '30 days' GROUP BY c.data ORDER BY c.data")
    else:
        cur.execute("SELECT c.data, COUNT(*) as total FROM consultas c WHERE status='atendido' AND c.data >= date('now','-30 days') GROUP BY c.data ORDER BY c.data")
    por_dia_rows = fetch_all(cur, cur.fetchall())

    cur.execute("SELECT u.nome as dentista, u.especialidade, SUM(CASE WHEN c.status='atendido' THEN 1 ELSE 0 END) as total FROM consultas c LEFT JOIN usuarios u ON u.id = c.dentista_id GROUP BY u.nome, u.especialidade ORDER BY total DESC")
    dents_base = fetch_all(cur, cur.fetchall())

    por_dentista = []
    for d in dents_base:
        nome = d['dentista']
        base_q = f"SELECT COUNT(*) FROM consultas c LEFT JOIN usuarios u ON u.id=c.dentista_id WHERE u.nome={p()} AND c.status='atendido'"
        cur.execute(base_q + f" AND {cast_d} = {hoje_expr}", (nome,))
        h = cur.fetchone()[0]
        cur.execute(base_q + f" AND {cast_d} >= {semana_expr}", (nome,))
        s = cur.fetchone()[0]
        cur.execute(base_q + f" AND {cast_d} >= {mes_expr}", (nome,))
        m = cur.fetchone()[0]
        cur.execute(base_q + f" AND {cast_d} >= {ano_expr}", (nome,))
        a = cur.fetchone()[0]
        por_dentista.append({'dentista': nome, 'especialidade': d['especialidade'] or '', 'hoje': h, 'semana': s, 'mes': m, 'ano': a, 'total': d['total'] or 0})

    conn.close()
    # Formatar datas para DD/MM/AAAA
    def fmt(data_str):
        try:
            from datetime import datetime
            return datetime.strptime(str(data_str)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            return data_str

    return jsonify({'totais': totais, 'por_dia': {'labels': [fmt(d['data']) for d in por_dia_rows], 'valores': [d['total'] for d in por_dia_rows]}, 'por_dentista': por_dentista})

@consultas.route('/consultas/status/<int:id>/<status>')
@tipo_required(['master', 'admin', 'operador', 'atendente'])
def atualizar_status(id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'UPDATE consultas SET status={p()} WHERE id={p()}', (status, id))
    conn.commit()
    conn.close()
    return redirect('/consultas')

@consultas.route('/consultas/detalhe/<int:id>')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def detalhe_consulta(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''SELECT c.*, p.nome as paciente, p.telefone as telefone_paciente,
        p.id as paciente_ficha_id, u.nome as dentista, u.especialidade as dentista_especialidade
        FROM consultas c LEFT JOIN pacientes p ON p.id = c.paciente_id
        LEFT JOIN usuarios u ON u.id = c.dentista_id WHERE c.id = {p()}''', (id,))
    c = fetch_one(cur, cur.fetchone())
    conn.close()
    if not c: return 'Consulta não encontrada'
    return render_template('consulta_detalhe.html', consulta=c)

@consultas.route('/emergencia')
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def emergencia():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM pacientes ORDER BY nome')
    pacs = fetch_all(cur, cur.fetchall())
    cur.execute("SELECT * FROM usuarios WHERE tipo = 'dentista' ORDER BY nome")
    dents = fetch_all(cur, cur.fetchall())
    conn.close()
    return render_template('emergencia.html', pacientes=pacs, dentistas=dents)

@consultas.route('/emergencia/salvar', methods=['POST'])
@tipo_required(['master', 'admin', 'operador', 'atendente', 'dentista'])
def salvar_emergencia():
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    procedimento = f"🚨 EMERGÊNCIA: {dados['procedimento']}"
    if dados.get('observacoes'):
        procedimento += f" | {dados['observacoes']}"
    cur.execute(
        f'INSERT INTO consultas (paciente_id, dentista_id, data, hora, procedimento, status) VALUES ({p()},{p()},{p()},{p()},{p()},{p()})',
        (dados['paciente_id'], dados['dentista_id'], dados['data'], dados['hora'], procedimento, 'confirmado')
    )
    conn.commit()
    conn.close()
    flash('🚨 Atendimento de emergência registrado!')
    return redirect('/consultas')

@consultas.route('/consultas/excluir/<int:id>')
@tipo_required(['master', 'admin'])
def excluir_consulta(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'DELETE FROM consultas WHERE id = {p()}', (id,))
    conn.commit()
    conn.close()
    flash('Consulta excluída!')
    return redirect('/consultas')

@consultas.route('/consultas/mover', methods=['POST'])
@tipo_required(['master', 'admin', 'operador', 'atendente'])
def mover_consulta():
    dados = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'UPDATE consultas SET data={p()}, hora={p()} WHERE id={p()}',
        (dados['data'], dados['hora'], dados['id']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
