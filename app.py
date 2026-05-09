from flask import Flask
import sqlite3

from routes.auth import auth
from routes.main import main
from routes.pacientes import pacientes
from routes.consultas import consultas

app = Flask(__name__)
app.secret_key = 'segredo_super'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 👤 USUÁRIOS (COM ESPECIALIDADE E CRO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            senha TEXT,
            tipo TEXT,
            especialidade TEXT,
            cro TEXT
        )
    ''')

    # 👥 PACIENTES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nome TEXT,
            data_nascimento TEXT,
            sexo TEXT,
            cpf TEXT,
            telefone TEXT,
            email TEXT,
            cep TEXT,
            logradouro TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            numero TEXT,
            complemento TEXT,
            responsavel_nome TEXT
        )
    ''')

    # 🦷 ANAMNESE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anamneses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            alergias TEXT,
            medicamentos TEXT,
            doencas TEXT,
            gravidez TEXT,
            observacoes TEXT
        )
    ''')

    # 📅 CONSULTAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            dentista_id INTEGER,
            data TEXT,
            hora TEXT,
            procedimento TEXT,
            status TEXT
        )
    ''')

    # 🗓️ ESCALA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escala_dentistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dentista_id INTEGER,
            dia_semana TEXT,
            hora_inicio TEXT,
            hora_fim TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prontuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            historico TEXT,
            diagnostico TEXT,
            tratamento TEXT,
            data TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prontuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            historico TEXT,
            diagnostico TEXT,
            tratamento TEXT,
            data TEXT
        )
    ''')

    # 👑 MASTER FIXO
    cursor.execute("SELECT * FROM usuarios WHERE tipo = 'master'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, tipo)
            VALUES (?, ?, ?, ?)
        ''', ('Administrador Master', 'master@clinica.com', '123456', 'master'))

    conn.commit()
    conn.close()

app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(pacientes)
app.register_blueprint(consultas)
from routes.dentistas import dentistas

app.register_blueprint(dentistas)

init_db()

if __name__ == '__main__':
    app.run(debug=True)