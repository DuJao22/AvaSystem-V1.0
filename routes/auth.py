# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from models.audit import log_action
import time

auth_bp = Blueprint('auth', __name__)

# Simple rate limiting in memory
login_attempts = {}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        
        # Simple rate limiting
        client_ip = request.environ.get('REMOTE_ADDR', '127.0.0.1')
        current_time = time.time()
        
        if client_ip in login_attempts:
            attempts, last_attempt = login_attempts[client_ip]
            if current_time - last_attempt < 60 and attempts >= 5:
                flash('Muitas tentativas de login. Tente novamente em 1 minuto.', 'error')
                return render_template('auth/login.html')
        
        # Validate input
        if not email or not senha:
            flash('Email e senha são obrigatórios', 'error')
            return render_template('auth/login.html')
        
        # Attempt authentication
        user = User.authenticate(email, senha)
        if user:
            session['user_id'] = user.id
            session['user_nome'] = user.nome
            session['user_perfil'] = user.perfil
            session['user_especialidade'] = user.especialidade
            
            # Reset login attempts
            if client_ip in login_attempts:
                del login_attempts[client_ip]
            
            flash(f'Bem-vindo(a), {user.nome}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            # Track failed attempt
            if client_ip not in login_attempts:
                login_attempts[client_ip] = [0, current_time]
            
            attempts, _ = login_attempts[client_ip]
            login_attempts[client_ip] = [attempts + 1, current_time]
            
            flash('Email ou senha incorretos', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Logout handler"""
    user_id = session.get('user_id')
    user_nome = session.get('user_nome')
    
    if user_id:
        log_action(user_id, 'logout', f'Logout realizado: {user_nome}')
    
    session.clear()
    flash('Logout realizado com sucesso', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/')
def index():
    """Root redirect"""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))
