"""
Script para popular o banco com dados de teste:
- 18 dentistas (3 por especialidade)
- Escalas para cada dentista
- 50 pacientes
- Consultas de -60 a +30 dias
"""
from db import get_db_connection, is_postgres
from datetime import date, timedelta
import random

def p():
    return '%s' if is_postgres() else '?'

especialidades = [
    'Endodontia', 'Cirurgia', 'Dentística',
    'Periodontia', 'Odontopediatria', 'Próteses'
]

dentistas_dados = [
    ('Dr. Carlos Mendes',    'carlos.mendes@clinica.com',    'Endodontia',      'CRO-12345'),
    ('Dra. Ana Ferreira',    'ana.ferreira@clinica.com',     'Endodontia',      'CRO-12346'),
    ('Dr. Paulo Rocha',      'paulo.rocha@clinica.com',      'Endodontia',      'CRO-12347'),
    ('Dra. Mariana Costa',   'mariana.costa@clinica.com',    'Cirurgia',        'CRO-12348'),
    ('Dr. Felipe Lima',      'felipe.lima@clinica.com',      'Cirurgia',        'CRO-12349'),
    ('Dra. Juliana Alves',   'juliana.alves@clinica.com',    'Cirurgia',        'CRO-12350'),
    ('Dr. Roberto Silva',    'roberto.silva@clinica.com',    'Dentística',      'CRO-12351'),
    ('Dra. Patricia Souza',  'patricia.souza@clinica.com',   'Dentística',      'CRO-12352'),
    ('Dr. Lucas Oliveira',   'lucas.oliveira@clinica.com',   'Dentística',      'CRO-12353'),
    ('Dra. Camila Santos',   'camila.santos@clinica.com',    'Periodontia',     'CRO-12354'),
    ('Dr. André Pereira',    'andre.pereira@clinica.com',    'Periodontia',     'CRO-12355'),
    ('Dra. Fernanda Lima',   'fernanda.lima@clinica.com',    'Periodontia',     'CRO-12356'),
    ('Dra. Beatriz Ramos',   'beatriz.ramos@clinica.com',    'Odontopediatria', 'CRO-12357'),
    ('Dr. Gabriel Nunes',    'gabriel.nunes@clinica.com',    'Odontopediatria', 'CRO-12358'),
    ('Dra. Larissa Dias',    'larissa.dias@clinica.com',     'Odontopediatria', 'CRO-12359'),
    ('Dr. Marcelo Teixeira', 'marcelo.teixeira@clinica.com', 'Próteses',        'CRO-12360'),
    ('Dra. Renata Castro',   'renata.castro@clinica.com',    'Próteses',        'CRO-12361'),
    ('Dr. Thiago Barbosa',   'thiago.barbosa@clinica.com',   'Próteses',        'CRO-12362'),
]

pacientes_dados = [
    ('João Silva', '1985-03-15', 'M', '111.111.111-11', '(11)91111-1111', 'joao.silva@email.com'),
    ('Maria Oliveira', '1990-07-22', 'F', '222.222.222-22', '(11)92222-2222', 'maria.oliveira@email.com'),
    ('Pedro Santos', '1978-11-30', 'M', '333.333.333-33', '(11)93333-3333', 'pedro.santos@email.com'),
    ('Ana Costa', '1995-01-10', 'F', '444.444.444-44', '(11)94444-4444', 'ana.costa@email.com'),
    ('Carlos Ferreira', '1982-06-05', 'M', '555.555.555-55', '(11)95555-5555', 'carlos.ferreira@email.com'),
    ('Fernanda Lima', '1988-09-18', 'F', '666.666.666-66', '(11)96666-6666', 'fernanda.lima@email.com'),
    ('Lucas Pereira', '1975-04-25', 'M', '777.777.777-77', '(11)97777-7777', 'lucas.pereira@email.com'),
    ('Juliana Rocha', '1993-12-08', 'F', '888.888.888-88', '(11)98888-8888', 'juliana.rocha@email.com'),
    ('Rafael Alves', '1980-08-14', 'M', '999.999.999-99', '(11)99999-9999', 'rafael.alves@email.com'),
    ('Patricia Souza', '1998-02-28', 'F', '101.010.101-01', '(11)90101-0101', 'patricia.souza@email.com'),
    ('Rodrigo Mendes', '1972-07-19', 'M', '121.212.121-21', '(11)91212-1212', 'rodrigo.mendes@email.com'),
    ('Camila Nunes', '1996-05-03', 'F', '131.313.131-31', '(11)93131-3131', 'camila.nunes@email.com'),
    ('Bruno Dias', '1983-10-27', 'M', '141.414.141-41', '(11)94141-4141', 'bruno.dias@email.com'),
    ('Larissa Teixeira', '1991-03-16', 'F', '151.515.151-51', '(11)95151-5151', 'larissa.teixeira@email.com'),
    ('Gustavo Castro', '1977-08-09', 'M', '161.616.161-61', '(11)96161-6161', 'gustavo.castro@email.com'),
    ('Vanessa Barbosa', '1994-01-23', 'F', '171.717.171-71', '(11)97171-7171', 'vanessa.barbosa@email.com'),
    ('Diego Ramos', '1986-06-12', 'M', '181.818.181-81', '(11)98181-8181', 'diego.ramos@email.com'),
    ('Aline Cardoso', '1999-11-05', 'F', '191.919.191-91', '(11)99191-9191', 'aline.cardoso@email.com'),
    ('Thiago Monteiro', '1973-04-30', 'M', '202.020.202-02', '(11)90202-0202', 'thiago.monteiro@email.com'),
    ('Renata Gomes', '1997-09-17', 'F', '212.121.212-12', '(11)92121-2121', 'renata.gomes@email.com'),
    ('Eduardo Pinto', '1981-02-14', 'M', '223.232.323-23', '(11)93232-3232', 'eduardo.pinto@email.com'),
    ('Isabela Freitas', '1992-07-28', 'F', '234.343.434-34', '(11)94343-4343', 'isabela.freitas@email.com'),
    ('Marcelo Correia', '1976-12-21', 'M', '245.454.545-45', '(11)95454-5454', 'marcelo.correia@email.com'),
    ('Stephanie Moura', '1995-05-06', 'F', '256.565.656-56', '(11)96565-6565', 'stephanie.moura@email.com'),
    ('Alexandre Cunha', '1984-10-19', 'M', '267.676.767-67', '(11)97676-7676', 'alexandre.cunha@email.com'),
    ('Bianca Araújo', '1989-03-04', 'F', '278.787.878-78', '(11)98787-8787', 'bianca.araujo@email.com'),
    ('Henrique Lopes', '1971-08-27', 'M', '289.898.989-89', '(11)99898-9898', 'henrique.lopes@email.com'),
    ('Natalia Carvalho', '1998-01-11', 'F', '290.909.090-90', '(11)90909-0909', 'natalia.carvalho@email.com'),
    ('Vinicius Melo', '1979-06-24', 'M', '301.010.101-10', '(11)91010-1010', 'vinicius.melo@email.com'),
    ('Leticia Vieira', '1993-11-17', 'F', '312.121.212-21', '(11)92121-2121', 'leticia.vieira@email.com'),
    ('Samuel Ribeiro', '1987-04-08', 'M', '323.232.323-32', '(11)93232-3232', 'samuel.ribeiro@email.com'),
    ('Priscila Martins', '1996-09-01', 'F', '334.343.434-43', '(11)94343-4343', 'priscila.martins@email.com'),
    ('Daniel Andrade', '1974-02-22', 'M', '345.454.545-54', '(11)95454-5454', 'daniel.andrade@email.com'),
    ('Raquel Fonseca', '1991-07-15', 'F', '356.565.656-65', '(11)96565-6565', 'raquel.fonseca@email.com'),
    ('Igor Tavares', '1982-12-08', 'M', '367.676.767-76', '(11)97676-7676', 'igor.tavares@email.com'),
    ('Monique Pires', '1997-05-31', 'F', '378.787.878-87', '(11)98787-8787', 'monique.pires@email.com'),
    ('Caio Nascimento', '1985-10-24', 'M', '389.898.989-98', '(11)99898-9898', 'caio.nascimento@email.com'),
    ('Viviane Xavier', '1990-03-09', 'F', '390.909.090-09', '(11)90909-0909', 'viviane.xavier@email.com'),
    ('Leandro Campos', '1978-08-02', 'M', '401.010.101-01', '(11)91010-1010', 'leandro.campos@email.com'),
    ('Tatiane Barros', '1994-01-25', 'F', '412.121.212-12', '(11)92121-2121', 'tatiane.barros@email.com'),
    ('Flávio Rezende', '1969-06-18', 'M', '423.232.323-23', '(11)93232-3232', 'flavio.rezende@email.com'),
    ('Cristina Azevedo', '1992-11-11', 'F', '434.343.434-34', '(11)94343-4343', 'cristina.azevedo@email.com'),
    ('Matheus Coelho', '1986-04-04', 'M', '445.454.545-45', '(11)95454-5454', 'matheus.coelho@email.com'),
    ('Débora Pacheco', '1999-09-27', 'F', '456.565.656-56', '(11)96565-6565', 'debora.pacheco@email.com'),
    ('Fábio Queiroz', '1980-02-20', 'M', '467.676.767-67', '(11)97676-7676', 'fabio.queiroz@email.com'),
    ('Silvia Drummond', '1988-07-13', 'F', '478.787.878-78', '(11)98787-8787', 'silvia.drummond@email.com'),
    ('Tiago Medeiros', '1975-12-06', 'M', '489.898.989-89', '(11)99898-9898', 'tiago.medeiros@email.com'),
    ('Elaine Figueiredo', '1995-05-30', 'F', '490.909.090-90', '(11)90909-0909', 'elaine.figueiredo@email.com'),
    ('Claudio Mendonça', '1983-10-23', 'M', '501.010.101-10', '(11)91010-1010', 'claudio.mendonca@email.com'),
    ('Soraya Brandão', '1991-03-16', 'F', '512.121.212-21', '(11)92121-2121', 'soraya.brandao@email.com'),
]

procedimentos = {
    'Endodontia':      ['Canal', 'Retratamento de canal'],
    'Cirurgia':        ['Extração simples', 'Extração de siso', 'Cirurgia periodontal'],
    'Dentística':      ['Restauração', 'Clareamento', 'Faceta'],
    'Periodontia':     ['Raspagem', 'Curetagem', 'Tratamento de gengivite'],
    'Odontopediatria': ['Consulta infantil', 'Selante', 'Fluorterapia'],
    'Próteses':        ['Prótese total', 'Prótese parcial', 'Coroa'],
}

dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
status_passado = ['atendido', 'atendido', 'atendido', 'faltou', 'cancelado']
horarios = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30',
            '13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00']

def run_popular():
    log = []
    conn = get_db_connection()
    cur = conn.cursor()

    log.append("Cadastrando dentistas...")
    dentista_ids = []
    for nome, email, esp, cro in dentistas_dados:
        try:
            cur.execute(
                f"INSERT INTO usuarios (nome, email, senha, tipo, especialidade, cro) VALUES ({p()},{p()},{p()},{p()},{p()},{p()})",
                (nome, email, '123456', 'dentista', esp, cro)
            )
            if is_postgres():
                cur.execute('SELECT lastval()')
                dentista_ids.append((cur.fetchone()[0], esp))
            else:
                dentista_ids.append((cur.lastrowid, esp))
        except Exception as e:
            cur.execute(f"SELECT id FROM usuarios WHERE email = {p()}", (email,))
            row = cur.fetchone()
            if row: dentista_ids.append((row[0], esp))

    log.append(f"{len(dentista_ids)} dentistas processados")

    log.append("Cadastrando escalas...")
    for did, esp in dentista_ids:
        dias = random.sample(dias_semana, 3)
        for dia in dias:
            try:
                cur.execute(
                    f"INSERT INTO escala_dentistas (dentista_id, dia_semana, hora_inicio, hora_fim) VALUES ({p()},{p()},{p()},{p()})",
                    (did, dia, '08:00', '18:00')
                )
            except: pass

    log.append("Cadastrando pacientes...")
    paciente_ids = []
    for nome, nasc, sexo, cpf, tel, email in pacientes_dados:
        try:
            cur.execute(
                f"INSERT INTO pacientes (nome, data_nascimento, sexo, cpf, telefone, email, cidade, estado) VALUES ({p()},{p()},{p()},{p()},{p()},{p()},{p()},{p()})",
                (nome, nasc, sexo, cpf, tel, email, 'São Paulo', 'SP')
            )
            if is_postgres():
                cur.execute('SELECT lastval()')
                paciente_ids.append(cur.fetchone()[0])
            else:
                paciente_ids.append(cur.lastrowid)
        except Exception as e:
            cur.execute(f"SELECT id FROM pacientes WHERE cpf = {p()}", (cpf,))
            row = cur.fetchone()
            if row: paciente_ids.append(row[0])

    log.append(f"{len(paciente_ids)} pacientes processados")

    log.append("Cadastrando consultas...")
    hoje = date.today()
    consultas_inseridas = 0
    horarios_usados = {}

    for delta in range(-60, 31):
        data = hoje + timedelta(days=delta)
        if data.weekday() >= 5:
            continue
        n = random.randint(2, 6)
        dents_dia = random.sample(dentista_ids, min(n, len(dentista_ids)))
        for did, esp in dents_dia:
            hora = random.choice(horarios)
            chave = (did, str(data), hora)
            if chave in horarios_usados:
                continue
            horarios_usados[chave] = True
            pac_id = random.choice(paciente_ids)
            proc = random.choice(procedimentos[esp])
            if delta < 0:
                status = random.choice(status_passado)
            elif delta == 0:
                status = random.choice(['agendado','confirmado','atendido'])
            else:
                status = random.choice(['agendado','confirmado'])
            try:
                cur.execute(
                    f"INSERT INTO consultas (paciente_id, dentista_id, data, hora, procedimento, status) VALUES ({p()},{p()},{p()},{p()},{p()},{p()})",
                    (pac_id, did, str(data), hora, proc, status)
                )
                consultas_inseridas += 1
            except: pass

    conn.commit()
    conn.close()
    log.append(f"{consultas_inseridas} consultas inseridas")
    log.append("\n✅ Concluído com sucesso!")
    return "\n".join(log)

if __name__ == '__main__':
    print(run_popular())
