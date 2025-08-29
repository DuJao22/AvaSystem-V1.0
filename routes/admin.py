# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from models.database import get_db_connection
from models.audit import get_audit_logs, count_audit_logs
from utils.auth import require_login, require_permission
from utils.helpers import get_specialties, get_locations

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@require_login
@require_permission(['admin'])
def index():
    """Admin dashboard"""
    return render_template('admin/index.html')

@admin_bp.route('/usuarios')
@require_login
@require_permission(['admin'])
def users():
    """Manage users"""
    users = User.get_all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@require_login
@require_permission(['admin'])
def new_user():
    """Create new user"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '').strip()
        perfil = request.form.get('perfil', '').strip()
        especialidade = request.form.get('especialidade', '').strip()
        
        # Validation
        errors = []
        
        if not nome:
            errors.append('Nome é obrigatório')
        
        if not email:
            errors.append('Email é obrigatório')
        elif User.get_by_email(email):
            errors.append('Email já está em uso')
        
        if not senha or len(senha) < 6:
            errors.append('Senha deve ter pelo menos 6 caracteres')
        
        if perfil not in ['admin', 'medico', 'coordenacao']:
            errors.append('Perfil inválido')
        
        if perfil == 'medico' and not especialidade:
            errors.append('Especialidade é obrigatória para médicos')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/user_form.html',
                                 nome=nome, email=email, perfil=perfil,
                                 especialidade=especialidade,
                                 specialties=get_specialties())
        
        try:
            user = User.create(
                nome=nome,
                email=email,
                senha=senha,
                perfil=perfil,
                especialidade=especialidade if perfil == 'medico' else None
            )
            
            if user:
                flash(f'Usuário {user.nome} criado com sucesso!', 'success')
            else:
                flash('Erro ao criar usuário', 'error')
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
    
    return render_template('admin/user_form.html',
                         specialties=get_specialties())

@admin_bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@require_login
@require_permission(['admin'])
def edit_user(id):
    """Edit user"""
    user = User.get_by_id(id)
    if not user:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        perfil = request.form.get('perfil', '').strip()
        especialidade = request.form.get('especialidade', '').strip()
        
        # Validation
        errors = []
        
        if not nome:
            errors.append('Nome é obrigatório')
        
        if not email:
            errors.append('Email é obrigatório')
        else:
            existing_user = User.get_by_email(email)
            if existing_user and existing_user.id != user.id:
                errors.append('Email já está em uso')
        
        if perfil not in ['admin', 'medico', 'coordenacao']:
            errors.append('Perfil inválido')
        
        if perfil == 'medico' and not especialidade:
            errors.append('Especialidade é obrigatória para médicos')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/user_form.html',
                                 user=user, nome=nome, email=email, 
                                 perfil=perfil, especialidade=especialidade,
                                 specialties=get_specialties())
        
        try:
            user.update(
                nome=nome,
                email=email,
                perfil=perfil,
                especialidade=especialidade if perfil == 'medico' else None
            )
            
            flash(f'Usuário {nome} atualizado com sucesso!', 'success')
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    return render_template('admin/user_form.html',
                         user=user,
                         specialties=get_specialties())

@admin_bp.route('/usuarios/<int:id>/desativar', methods=['POST'])
@require_login
@require_permission(['admin'])
def deactivate_user(id):
    """Deactivate user"""
    user = User.get_by_id(id)
    if not user:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('admin.users'))
    
    # Prevent self-deactivation
    if user.id == session.get('user_id'):
        flash('Você não pode desativar sua própria conta', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        user.deactivate()
        flash(f'Usuário {user.nome} desativado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao desativar usuário: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/especialidades')
@require_login
@require_permission(['admin'])
def specialties():
    """Manage specialties"""
    specialties = get_specialties()
    return render_template('admin/specialties.html', specialties=specialties)

@admin_bp.route('/especialidades/nova', methods=['POST'])
@require_login
@require_permission(['admin'])
def new_specialty():
    """Create new specialty"""
    nome = request.form.get('nome', '').strip()
    
    if not nome:
        flash('Nome da especialidade é obrigatório', 'error')
        return redirect(url_for('admin.specialties'))
    
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO especialidades (nome) VALUES (?)
        """, (nome,))
        conn.commit()
        
        flash(f'Especialidade {nome} criada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao criar especialidade: {str(e)}', 'error')
    
    return redirect(url_for('admin.specialties'))

@admin_bp.route('/locais')
@require_login
@require_permission(['admin'])
def locations():
    """Manage locations"""
    locations = get_locations()
    return render_template('admin/locations.html', locations=locations)

@admin_bp.route('/locais/novo', methods=['POST'])
@require_login
@require_permission(['admin'])
def new_location():
    """Create new location"""
    nome = request.form.get('nome', '').strip()
    
    if not nome:
        flash('Nome do local é obrigatório', 'error')
        return redirect(url_for('admin.locations'))
    
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO locais (nome) VALUES (?)
        """, (nome,))
        conn.commit()
        
        flash(f'Local {nome} criado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao criar local: {str(e)}', 'error')
    
    return redirect(url_for('admin.locations'))

@admin_bp.route('/auditoria')
@require_login
@require_permission(['admin'])
def audit():
    """View audit logs"""
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    logs = get_audit_logs(limit=per_page, offset=offset)
    total = count_audit_logs()
    
    has_next = offset + per_page < total
    has_prev = page > 1
    
    return render_template('admin/audit.html',
                         logs=logs,
                         page=page,
                         has_next=has_next,
                         has_prev=has_prev)

@admin_bp.route('/reset-pacientes', methods=['POST'])
@require_login
@require_permission(['admin'])
def reset_patients():
    """Reset patient data while keeping doctors"""
    confirmation = request.form.get('confirmation', '').strip()
    
    if confirmation != 'CONFIRMO':
        flash('Você deve digitar "CONFIRMO" para confirmar a operação', 'error')
        return redirect(url_for('admin.index'))
    
    try:
        conn = get_db_connection()
        
        # Start transaction
        conn.execute('BEGIN')
        
        # Delete procedures first (foreign key constraint)
        conn.execute('DELETE FROM procedimentos')
        
        # Delete evaluation therapies (foreign key constraint)
        conn.execute('DELETE FROM avaliacao_terapias')
        
        # Delete evaluations (foreign key constraint)
        conn.execute('DELETE FROM avaliacoes')
        
        # Finally delete patients
        conn.execute('DELETE FROM pacientes')
        
        # Add audit log
        from models.audit import log_action
        log_action(
            user_id=session.get('user_id'),
            acao='RESET_PACIENTES',
            detalhe='Administrador resetou todos os dados de pacientes'
        )
        
        conn.commit()
        
        flash('Todos os dados de pacientes foram removidos com sucesso! Os médicos foram mantidos.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao resetar dados: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))
