from flask import Flask
from db import get_db_connection, is_postgres
from routes.auth import auth
from routes.main import main
from routes.pacientes import pacientes
from routes.consultas import consultas
from routes.dentistas import dentistas
from routes.perfil import perfil

app = Flask(__name__)
app.secret_key = 'segredo_super'

# Filtro para mascarar dados sensíveis
@app.template_filter('mascarar_cpf')
def mascarar_cpf(valor):
    if not valor: return '—'
    v = str(valor).replace('.','').replace('-','')
    return f'***.{v[3:6]}.***-**' if len(v) >= 9 else '***'

@app.template_filter('mascarar_telefone')
def mascarar_telefone(valor):
    if not valor: return '—'
    v = str(valor)
    if len(v) >= 4:
        return v[:3] + ' *****-' + v[-2:]
    return '****'

@app.template_filter('mascarar_email')
def mascarar_email(valor):
    if not valor: return '—'
    partes = str(valor).split('@')
    if len(partes) == 2:
        usuario = partes[0]
        return usuario[0] + '****@' + partes[1]
    return '****'

@app.template_filter('mascarar_nome')
def mascarar_nome(valor):
    if not valor: return '—'
    partes = str(valor).split()
    if len(partes) >= 2:
        return partes[0] + ' ' + ' '.join('*' * len(p) for p in partes[1:])
    return valor

# Filtro para formatar datas no formato DD/MM/AAAA
@app.template_filter('formatar_data')
def formatar_data(valor):
    if not valor:
        return '—'
    try:
        from datetime import datetime
        if '/' in str(valor):
            return valor
        dt = datetime.strptime(str(valor)[:10], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except:
        return valor

app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(pacientes)
app.register_blueprint(consultas)
app.register_blueprint(dentistas)
app.register_blueprint(perfil)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_postgres():
        pk = 'SERIAL PRIMARY KEY'
    else:
        pk = 'INTEGER PRIMARY KEY AUTOINCREMENT'

    tables = [
        f'''CREATE TABLE IF NOT EXISTS usuarios (
            id {pk}, nome TEXT, email TEXT UNIQUE, senha TEXT, tipo TEXT,
            especialidade TEXT, cro TEXT)''',
        f'''CREATE TABLE IF NOT EXISTS pacientes (
            id {pk}, usuario_id INTEGER, nome TEXT, data_nascimento TEXT,
            sexo TEXT, cpf TEXT, telefone TEXT, email TEXT, cep TEXT,
            logradouro TEXT, bairro TEXT, cidade TEXT, estado TEXT,
            numero TEXT, complemento TEXT, responsavel_nome TEXT)''',
        f'''CREATE TABLE IF NOT EXISTS anamneses (
            id {pk}, paciente_id INTEGER, alergias TEXT, medicamentos TEXT,
            doencas TEXT, gravidez TEXT, observacoes TEXT)''',
        f'''CREATE TABLE IF NOT EXISTS consultas (
            id {pk}, paciente_id INTEGER, dentista_id INTEGER,
            data TEXT, hora TEXT, procedimento TEXT, status TEXT)''',
        f'''CREATE TABLE IF NOT EXISTS escala_dentistas (
            id {pk}, dentista_id INTEGER, dia_semana TEXT,
            hora_inicio TEXT, hora_fim TEXT)''',
        f'''CREATE TABLE IF NOT EXISTS prontuario (
            id {pk}, paciente_id INTEGER, historico TEXT,
            diagnostico TEXT, tratamento TEXT, data TEXT)''',
        f'''CREATE TABLE IF NOT EXISTS atendimentos (
            id {pk}, paciente_id INTEGER, dentista_id INTEGER,
            data TEXT, queixa TEXT, diagnostico TEXT, tratamento TEXT,
            prescricao TEXT, observacoes TEXT, retorno TEXT)''',
    ]

    for sql in tables:
        cursor.execute(sql)

    # Colunas extras na anamnese
    if is_postgres():
        for col in ['tratamento_medico','tratamento_anterior','sensibilidade',
                    'bruxismo','sangramento','protese','habitos','doencas_outras']:
            try:
                cursor.execute(f'ALTER TABLE anamneses ADD COLUMN IF NOT EXISTS {col} TEXT')
            except:
                pass

    cursor.execute("SELECT * FROM usuarios WHERE tipo = 'master'")
    if not cursor.fetchone():
        p = '%s' if is_postgres() else '?'
        cursor.execute(
            f'INSERT INTO usuarios (nome, email, senha, tipo) VALUES ({p},{p},{p},{p})',
            ('Administrador Master', 'master@clinica.com', '123456', 'master')
        )

    conn.commit()
    conn.close()

init_db()

@app.route('/setup/popular-dados-clinica-2026')
def popular_dados_rota():
    """Rota secreta para popular dados de teste - remover após uso"""
    try:
        from popular_dados import run_popular
        result = run_popular()
        return f'<pre>{result}</pre>'
    except Exception as e:
        return f'<pre>Erro: {e}</pre>'

if __name__ == '__main__':
    app.run(debug=True)
