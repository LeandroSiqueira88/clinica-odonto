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
    ]

    for sql in tables:
        cursor.execute(sql)

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

if __name__ == '__main__':
    app.run(debug=True)
