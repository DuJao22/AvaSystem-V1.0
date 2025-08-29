# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from functools import wraps
from flask import session, redirect, url_for, flash
from models.user import User

def require_login(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página', 'error')
            return redirect(url_for('auth.login'))
        
        # Verify user still exists and is active
        user = User.get_by_id(session['user_id'])
        if not user or not user.is_active():
            session.clear()
            flash('Sessão inválida. Faça login novamente.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_permission(allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_perfil = session.get('user_perfil')
            
            if user_perfil not in allowed_roles:
                flash('Você não tem permissão para acessar esta página', 'error')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current logged in user"""
    user_id = session.get('user_id')
    if user_id:
        return User.get_by_id(user_id)
    return None

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

def has_permission(action):
    """Check if current user has permission for action"""
    user_perfil = session.get('user_perfil')
    
    permissions = {
        'admin': ['manage_users', 'manage_settings', 'view_all', 'manage_all'],
        'medico': ['create_evaluation', 'pull_patient', 'update_own_procedures'],
        'coordenacao': ['create_patient', 'view_distribution', 'administrative_release']
    }
    
    return action in permissions.get(user_perfil or '', [])
