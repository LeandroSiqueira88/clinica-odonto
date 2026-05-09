from flask import Blueprint, render_template, request, redirect, flash, session
import sqlite3
from routes.utils import tipo_required
from flask import jsonify


consultas = Blueprint('consultas', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

from datetime import datetime

def obter_dia_semana(data):
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    dt = datetime.strptime(data, "%Y-%m-%d")
    return dias[dt.weekday()]

# 📅 AGENDA
@consultas.route('/consultas')
def agenda():
    dentista_id = request.args.get('dentista_id')
    especialidade = request.args.get('especialidade')

    conn = get_db_connection()

    query = '''
        SELECT c.*, p.nome as paciente, u.nome as dentista, u.especialidade
        FROM consultas c
        LEFT JOIN pacientes p ON p.id = c.paciente_id
        LEFT JOIN usuarios u ON u.id = c.dentista_id
        WHERE 1=1
    '''

    params = []

    if dentista_id:
        query += " AND c.dentista_id = ?"
        params.append(dentista_id)

    if especialidade:
        query += " AND u.especialidade = ?"
        params.append(especialidade)

    query += " ORDER BY c.data, c.hora"

    consultas = conn.execute(query, params).fetchall()

    dentistas = conn.execute(
        "SELECT * FROM usuarios WHERE tipo='dentista'"
    ).fetchall()

    conn.close()

    return render_template(
        'agenda.html',
        consultas=consultas,
        dentistas=dentistas
    )

# ➕ NOVA CONSULTA
@consultas.route('/consultas/nova')
@tipo_required(['master','admin','atendente'])
def nova_consulta():
    conn = get_db_connection()

    pacientes = conn.execute("SELECT * FROM pacientes").fetchall()
    dentistas = conn.execute("SELECT * FROM usuarios WHERE tipo = 'dentista'").fetchall()

    conn.close()

    return render_template('nova_consulta.html', pacientes=pacientes, dentistas=dentistas)


# 💾 SALVAR CONSULTA
@consultas.route('/consultas/salvar', methods=['POST'])
@tipo_required(['master','admin','atendente'])
def salvar_consulta():
    dados = request.form

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO consultas (paciente_id, dentista_id, data, hora, procedimento, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        dados['paciente_id'],
        dados['dentista_id'],
        dados['data'],
        dados['hora'],
        dados['procedimento'],
        'agendado'
    ))

    conn.commit()
    conn.close()

    flash('Consulta agendada com sucesso!')
    return redirect('/consultas')


# 📅 ESCALA
@consultas.route('/escala')
@tipo_required(['master','admin'])
def escala():
    conn = get_db_connection()

    escala = conn.execute('''
        SELECT e.*, u.nome as dentista_nome
        FROM escala_dentistas e
        LEFT JOIN usuarios u ON u.id = e.dentista_id
    ''').fetchall()

    conn.close()

    return render_template('escala.html', escala=escala)


# ➕ NOVA ESCALA
@consultas.route('/escala/nova')
@tipo_required(['master','admin'])
def nova_escala():
    conn = get_db_connection()

    dentistas = conn.execute(
        "SELECT * FROM usuarios WHERE tipo = 'dentista'"
    ).fetchall()

    conn.close()

    return render_template('nova_escala.html', dentistas=dentistas)


# 💾 SALVAR ESCALA
@consultas.route('/escala/salvar', methods=['POST'])
@tipo_required(['master','admin'])
def salvar_escala():
    dados = request.form

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO escala_dentistas (dentista_id, dia_semana, hora_inicio, hora_fim)
        VALUES (?, ?, ?, ?)
    ''', (
        dados['dentista_id'],
        dados['dia_semana'],
        dados['hora_inicio'],
        dados['hora_fim']
    ))

    conn.commit()
    conn.close()

    flash('Escala cadastrada!')
    return redirect('/escala')


# ✏️ EDITAR ESCALA
@consultas.route('/escala/editar/<int:id>')
@tipo_required(['master','admin'])
def editar_escala(id):
    conn = get_db_connection()

    escala = conn.execute(
        "SELECT * FROM escala_dentistas WHERE id = ?", (id,)
    ).fetchone()

    dentistas = conn.execute(
        "SELECT * FROM usuarios WHERE tipo = 'dentista'"
    ).fetchall()

    conn.close()

    return render_template('editar_escala.html', escala=escala, dentistas=dentistas)


# 💾 ATUALIZAR ESCALA
@consultas.route('/escala/atualizar/<int:id>', methods=['POST'])
@tipo_required(['master','admin'])
def atualizar_escala(id):
    dados = request.form

    conn = get_db_connection()
    conn.execute('''
        UPDATE escala_dentistas
        SET dentista_id=?, dia_semana=?, hora_inicio=?, hora_fim=?
        WHERE id=?
    ''', (
        dados['dentista_id'],
        dados['dia_semana'],
        dados['hora_inicio'],
        dados['hora_fim'],
        id
    ))

    conn.commit()
    conn.close()

    flash('Escala atualizada!')
    return redirect('/escala')

@consultas.route('/minha_area/nova_consulta')
def nova_consulta_paciente():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    # pegar paciente logado
    paciente = conn.execute(
        "SELECT * FROM pacientes WHERE usuario_id = ?",
        (session['usuario_id'],)
    ).fetchone()

    dentistas = conn.execute(
        "SELECT * FROM usuarios WHERE tipo = 'dentista'"
    ).fetchall()

    conn.close()

    return render_template(
        'nova_consulta_paciente.html',
        paciente=paciente,
        dentistas=dentistas
    )

@consultas.route('/minha_area/salvar_consulta', methods=['POST'])
def salvar_consulta_paciente():
    if 'usuario_id' not in session:
        return redirect('/login')

    dados = request.form

    conn = get_db_connection()

    # pegar paciente
    paciente = conn.execute(
        "SELECT * FROM pacientes WHERE usuario_id = ?",
        (session['usuario_id'],)
    ).fetchone()

    # 🚫 BLOQUEIO 1 — horário já ocupado
    conflito = conn.execute('''
        SELECT * FROM consultas
        WHERE dentista_id = ? AND data = ? AND hora = ?
    ''', (
        dados['dentista_id'],
        dados['data'],
        dados['hora']
    )).fetchone()

    if conflito:
        conn.close()
        return "Horário já ocupado!"

    # 🚫 BLOQUEIO 2 — fora da escala
    escala = conn.execute('''
        SELECT * FROM escala_dentistas
        WHERE dentista_id = ? AND dia_semana = ?
    ''', (
        dados['dentista_id'],
        obter_dia_semana(dados['data'])
    )).fetchone()

    if not escala:
        conn.close()
        return "Dentista não atende nesse dia!"

    if not (escala['hora_inicio'] <= dados['hora'] <= escala['hora_fim']):
        conn.close()
        return "Fora do horário do dentista!"

    # 💾 salvar consulta
    conn.execute('''
        INSERT INTO consultas (paciente_id, dentista_id, data, hora, procedimento, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        paciente['id'],
        dados['dentista_id'],
        dados['data'],
        dados['hora'],
        dados['procedimento'],
        'agendado'
    ))

    conn.commit()
    conn.close()

    return redirect('/minha_area')

@consultas.route('/consultas/horarios_disponiveis')
def horarios_disponiveis():
    dentista_id = request.args.get('dentista_id')
    data = request.args.get('data')

    conn = get_db_connection()

    # 🧠 dia da semana
    dia_semana = obter_dia_semana(data)

    escala = conn.execute('''
        SELECT * FROM escala_dentistas
        WHERE dentista_id = ? AND dia_semana = ?
    ''', (dentista_id, dia_semana)).fetchone()

    if not escala:
        return jsonify([])

    # 🕐 gerar horários (30 em 30 min)
    horarios = []
    inicio = int(escala['hora_inicio'].split(':')[0])
    fim = int(escala['hora_fim'].split(':')[0])

    for h in range(inicio, fim + 1):
        horarios.append(f"{h:02d}:00")
        horarios.append(f"{h:02d}:30")

    # ❌ remover horários ocupados
    ocupados = conn.execute('''
        SELECT hora FROM consultas
        WHERE dentista_id = ? AND data = ?
    ''', (dentista_id, data)).fetchall()

    ocupados = [o['hora'] for o in ocupados]

    livres = [h for h in horarios if h not in ocupados]

    conn.close()

    return jsonify(livres)

@consultas.route('/consultas/verificar_dia')
def verificar_dia():
    dentista_id = request.args.get('dentista_id')
    data = request.args.get('data')

    dia = obter_dia_semana(data)

    conn = get_db_connection()

    escala = conn.execute('''
        SELECT * FROM escala_dentistas
        WHERE dentista_id = ? AND dia_semana = ?
    ''', (dentista_id, dia)).fetchone()

    conn.close()

    return {"valido": bool(escala)}

@consultas.route('/consultas/agenda_dentista')
def agenda_dentista():
    dentista_id = request.args.get('dentista_id')
    data = request.args.get('data')

    conn = get_db_connection()

    consultas = conn.execute('''
        SELECT * FROM consultas
        WHERE dentista_id = ? AND data = ?
    ''', (dentista_id, data)).fetchall()

    conn.close()

    return render_template('agenda_dentista.html', consultas=consultas)

@consultas.route('/consultas/painel')
@tipo_required(['master','admin','atendente'])
def painel_agenda():
    conn = get_db_connection()

    consultas = conn.execute('''
        SELECT c.*, p.nome as paciente, u.nome as dentista
        FROM consultas c
        LEFT JOIN pacientes p ON p.id = c.paciente_id
        LEFT JOIN usuarios u ON u.id = c.dentista_id
        ORDER BY data, hora
    ''').fetchall()

    conn.close()

    return render_template('painel_agenda.html', consultas=consultas)

@consultas.route('/consultas/eventos')
def eventos():
    conn = get_db_connection()

    consultas = conn.execute('''
        SELECT c.*, p.nome as paciente
        FROM consultas c
        LEFT JOIN pacientes p ON p.id = c.paciente_id
    ''').fetchall()

    eventos = []

    for c in consultas:
        eventos.append({
            "title": f"{c['paciente']} - {c['procedimento']}",
            "start": f"{c['data']}T{c['hora']}",
        })

    conn.close()

    return jsonify(eventos)

@consultas.route('/agenda_calendario')
def agenda_calendario():
    return render_template('agenda_calendario.html')

@consultas.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@consultas.route('/dashboard/dados')
def dashboard_dados():
    conn = get_db_connection()

    dados = conn.execute('''
        SELECT data, COUNT(*) as total
        FROM consultas
        GROUP BY data
        ORDER BY data
    ''').fetchall()

    conn.close()

    return jsonify({
        "labels": [d['data'] for d in dados],
        "valores": [d['total'] for d in dados]
    })

@consultas.route('/consultas/status/<int:id>/<status>')
def atualizar_status(id, status):
    conn = get_db_connection()

    conn.execute(
        "UPDATE consultas SET status = ? WHERE id = ?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect('/consultas')

@consultas.route('/consultas/detalhe/<int:id>')
def detalhe_consulta(id):
    conn = get_db_connection()

    consulta = conn.execute('''
        SELECT c.*, p.nome as paciente, u.nome as dentista
        FROM consultas c
        LEFT JOIN pacientes p ON p.id = c.paciente_id
        LEFT JOIN usuarios u ON u.id = c.dentista_id
        WHERE c.id = ?
    ''', (id,)).fetchone()

    conn.close()

    if not consulta:
        return "Consulta não encontrada"

    return render_template('consulta_detalhe.html', consulta=consulta)

@consultas.route('/consultas/mover', methods=['POST'])
def mover_consulta():
    dados = request.get_json()

    conn = get_db_connection()

    conn.execute('''
        UPDATE consultas
        SET data = ?, hora = ?
        WHERE id = ?
    ''', (
        dados['data'],
        dados['hora'],
        dados['id']
    ))

    conn.commit()
    conn.close()

    return {'ok': True}