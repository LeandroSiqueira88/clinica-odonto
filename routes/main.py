from flask import Blueprint, render_template, session, redirect, request
from db import get_db_connection, is_postgres
from routes.utils import rows_as_dicts, row_as_dict

main = Blueprint('main', __name__)

def p():
    return '%s' if is_postgres() else '?'

@main.route('/')
def home():
    if 'usuario_id' not in session:
        return redirect('/login')
    if session['usuario_tipo'] == 'cliente':
        return redirect('/minha_area')
    return render_template('index.html')

@main.route('/minha_area')
def minha_area():
    if 'usuario_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''
        SELECT c.*, u.nome as dentista_nome
        FROM consultas c
        LEFT JOIN usuarios u ON u.id = c.dentista_id
        LEFT JOIN pacientes p ON p.id = c.paciente_id
        WHERE p.usuario_id = {p()}
        ORDER BY c.data, c.hora
    ''', (session['usuario_id'],))
    rows = cur.fetchall()
    consultas = rows_as_dicts(rows, cur) if is_postgres() else rows
    conn.close()
    return render_template('minha_area.html', consultas=consultas)


@main.route('/minha_area/minha_anamnese')
def minha_anamnese():
    if 'usuario_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM pacientes WHERE usuario_id = {"%s" if is_postgres() else "?"}', (session['usuario_id'],))
    pac = row_as_dict(cur.fetchone(), cur) if is_postgres() else cur.fetchone()
    anamnese = None
    if pac:
        pid = pac['id']
        cur.execute(f'SELECT * FROM anamneses WHERE paciente_id = {"%s" if is_postgres() else "?"}', (pid,))
        row = cur.fetchone()
        anamnese = row_as_dict(row, cur) if is_postgres() else row
    conn.close()
    return render_template('minha_anamnese.html', anamnese=anamnese)

@main.route('/minha_area/salvar_anamnese', methods=['POST'])
def salvar_minha_anamnese():
    if 'usuario_id' not in session:
        return redirect('/login')
    from flask import flash
    dados = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    ph = '%s' if is_postgres() else '?'

    cur.execute(f'SELECT * FROM pacientes WHERE usuario_id = {ph}', (session['usuario_id'],))
    pac = row_as_dict(cur.fetchone(), cur) if is_postgres() else cur.fetchone()
    if not pac:
        conn.close()
        return redirect('/minha_area')

    pid = pac['id']
    doencas = ','.join(dados.getlist('doencas'))

    cur.execute(f'SELECT id FROM anamneses WHERE paciente_id = {ph}', (pid,))
    existe = cur.fetchone()

    vals = (dados.get('tratamento_medico'), dados.get('medicamentos'), dados.get('alergias'),
            doencas, dados.get('doencas_outras'), dados.get('tratamento_anterior'),
            dados.get('sensibilidade'), dados.get('bruxismo'), dados.get('sangramento'),
            dados.get('protese'), dados.get('gravidez'), dados.get('habitos'),
            dados.get('observacoes'))

    if existe:
        cur.execute(f'''UPDATE anamneses SET tratamento_medico={ph}, medicamentos={ph}, alergias={ph},
            doencas={ph}, doencas_outras={ph}, tratamento_anterior={ph}, sensibilidade={ph},
            bruxismo={ph}, sangramento={ph}, protese={ph}, gravidez={ph}, habitos={ph},
            observacoes={ph} WHERE paciente_id={ph}''', vals + (pid,))
    else:
        cur.execute(f'''INSERT INTO anamneses (tratamento_medico, medicamentos, alergias, doencas,
            doencas_outras, tratamento_anterior, sensibilidade, bruxismo, sangramento,
            protese, gravidez, habitos, observacoes, paciente_id)
            VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})''', vals + (pid,))

    conn.commit()
    conn.close()
    flash('Anamnese salva com sucesso!')
    return redirect('/minha_area')
