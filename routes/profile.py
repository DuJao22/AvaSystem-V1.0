# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from utils.auth import require_login, get_current_user
from models.user import User

profile_bp = Blueprint('profile', __name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads/profile'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure upload folder exists"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@profile_bp.route('/')
@require_login
def index():
    """User profile page"""
    user = get_current_user()
    if not user:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('auth.login'))
    return render_template('profile/index.html', user=user)

@profile_bp.route('/editar', methods=['GET', 'POST'])
@require_login
def edit():
    """Edit user profile"""
    user = get_current_user()
    if not user:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        foto_perfil = None
        
        # Validation
        errors = []
        
        if not nome:
            errors.append('Nome é obrigatório')
        
        # Handle file upload
        if 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            if file and file.filename and allowed_file(file.filename):
                ensure_upload_folder()
                filename = secure_filename(file.filename)
                # Add user ID to filename to avoid conflicts
                filename = f"user_{user.id}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                try:
                    file.save(filepath)
                    foto_perfil = f"uploads/profile/{filename}"
                except Exception as e:
                    errors.append(f'Erro ao fazer upload da foto: {str(e)}')
            elif file and file.filename and not allowed_file(file.filename):
                errors.append('Formato de arquivo não permitido. Use PNG, JPG, JPEG ou GIF')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile/edit.html', user=user)
        
        try:
            success, message = user.update_profile(nome=nome, foto_perfil=foto_perfil)
            if success:
                # Update session data
                session['user_nome'] = user.nome
                flash(message, 'success')
                return redirect(url_for('profile.index'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            flash(f'Erro ao atualizar perfil: {str(e)}', 'error')
    
    return render_template('profile/edit.html', user=user)

@profile_bp.route('/senha', methods=['GET', 'POST'])
@require_login
def change_password():
    """Change user password"""
    user = get_current_user()
    if not user:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        # Validation
        errors = []
        
        if not senha_atual:
            errors.append('Senha atual é obrigatória')
        
        if not nova_senha:
            errors.append('Nova senha é obrigatória')
        elif len(nova_senha) < 6:
            errors.append('Nova senha deve ter pelo menos 6 caracteres')
        
        if nova_senha != confirmar_senha:
            errors.append('Confirmação de senha não confere')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile/change_password.html')
        
        try:
            success, message = user.change_password(senha_atual, nova_senha)
            if success:
                flash(message, 'success')
                return redirect(url_for('profile.index'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            flash(f'Erro ao alterar senha: {str(e)}', 'error')
    
    return render_template('profile/change_password.html')