from flask import Blueprint, render_template, request, redirect, session, flash
from db import get_db_connection, is_postgres
from routes.utils import row_as_dict

perfil = Blueprint('perfil', __name__)

def p():
    return '%s' if is_postgres() else '?'

@perfil.route('/perfil')
def meu_perfil():
    if 'usuario_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM usuarios WHERE id = {p()}', (session['usuario_id'],))
    row = cur.fetchone()
    usuario = row_as_dict(row, cur) if is_postgres() else row

    paciente = None
    if session.get('usuario_tipo') == 'cliente':
        cur.execute(f'SELECT * FROM pacientes WHERE usuario_id = {p()}', (session['usuario_id'],))
        row2 = cur.fetchone()
        paciente = row_as_dict(row2, cur) if is_postgres() else row2

    conn.close()
    return render_template('meu_perfil.html', usuario=usuario, paciente=paciente, erro=None, sucesso=None)

@perfil.route('/perfil/salvar', methods=['POST'])
def salvar_perfil():
    if 'usuario_id' not in session:
        return redirect('/login')

    dados = request.form
    uid = session['usuario_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Verificar senha atual se quiser trocar
    senha_atual   = dados.get('senha_atual', '').strip()
    senha_nova    = dados.get('senha_nova', '').strip()
    senha_confirma= dados.get('senha_confirma', '').strip()

    cur.execute(f'SELECT * FROM usuarios WHERE id = {p()}', (uid,))
    row = cur.fetchone()
    usuario = row_as_dict(row, cur) if is_postgres() else row

    if senha_nova:
        if not senha_atual:
            conn.close()
            return render_template('meu_perfil.html', usuario=usuario, paciente=None,
                erro='Informe a senha atual para alterá-la.', sucesso=None)
        if usuario['senha'] != senha_atual:
            conn.close()
            return render_template('meu_perfil.html', usuario=usuario, paciente=None,
                erro='Senha atual incorreta.', sucesso=None)
        if senha_nova != senha_confirma:
            conn.close()
            return render_template('meu_perfil.html', usuario=usuario, paciente=None,
                erro='A nova senha e a confirmação não coincidem.', sucesso=None)
        cur.execute(f'UPDATE usuarios SET nome={p()}, email={p()}, senha={p()} WHERE id={p()}',
            (dados['nome'], dados['email'], senha_nova, uid))
    else:
        cur.execute(f'UPDATE usuarios SET nome={p()}, email={p()} WHERE id={p()}',
            (dados['nome'], dados['email'], uid))

    # Atualizar dados do paciente se for cliente
    if session.get('usuario_tipo') == 'cliente':
        cur.execute(f'SELECT id FROM pacientes WHERE usuario_id = {p()}', (uid,))
        pac = cur.fetchone()
        if pac:
            pid = pac[0]
            cur.execute(f'''UPDATE pacientes SET telefone={p()}, data_nascimento={p()},
                cep={p()}, logradouro={p()}, numero={p()}, bairro={p()}, cidade={p()}, estado={p()}
                WHERE id={p()}''',
                (dados.get('telefone'), dados.get('data_nascimento'), dados.get('cep'),
                 dados.get('logradouro'), dados.get('numero'), dados.get('bairro'),
                 dados.get('cidade'), dados.get('estado'), pid))

    session['usuario_nome'] = dados['nome']
    conn.commit()
    conn.close()
    flash('Perfil atualizado com sucesso!')
    return redirect('/perfil')
