# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.evaluation import Evaluation
from models.patient import Patient
from models.user import User
from config import Config
from utils.auth import require_login, require_permission
from utils.helpers import validate_date, get_specialties, get_locations

evaluations_bp = Blueprint('evaluations', __name__)

@evaluations_bp.route('/')
@require_login
def list():
    """List evaluations with filters"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    # Build filters
    filters = {}
    
    user_perfil = session.get('user_perfil')
    user_id = session.get('user_id')
    
    # If doctor, show only their evaluations by default
    if user_perfil == 'medico':
        filters['medico_id'] = int(request.args.get('medico_id', user_id))
    elif request.args.get('medico_id'):
        filters['medico_id'] = int(request.args.get('medico_id'))
    
    if request.args.get('especialidade'):
        filters['especialidade'] = request.args.get('especialidade')
    
    if request.args.get('data_inicio'):
        filters['data_inicio'] = request.args.get('data_inicio')
    
    if request.args.get('data_fim'):
        filters['data_fim'] = request.args.get('data_fim')
    
    evaluations = Evaluation.get_all(filters, limit=per_page, offset=offset)
    total = Evaluation.count_all(filters)
    
    has_next = offset + per_page < total
    has_prev = page > 1
    
    # Get filter options
    doctors = User.get_all() if user_perfil != 'medico' else []
    specialties = get_specialties()
    
    return render_template('evaluations/list.html',
                         evaluations=evaluations,
                         doctors=doctors,
                         specialties=specialties,
                         filters=filters,
                         page=page,
                         has_next=has_next,
                         has_prev=has_prev)

@evaluations_bp.route('/nova', methods=['GET', 'POST'])
@require_login
@require_permission(['medico', 'admin'])
def new():
    """Create new evaluation"""
    if request.method == 'POST':
        paciente_id = request.form.get('paciente_id')
        especialidade = request.form.get('especialidade', '').strip()
        local = request.form.get('local', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        terapias = request.form.getlist('terapias')
        
        # Validation
        errors = []
        
        if not paciente_id:
            errors.append('Paciente é obrigatório')
        else:
            try:
                paciente_id = int(paciente_id)
                patient = Patient.get_by_id(paciente_id)
                if not patient:
                    errors.append('Paciente não encontrado')
            except ValueError:
                errors.append('Paciente inválido')
        
        if not especialidade:
            errors.append('Especialidade é obrigatória')
        
        if not local:
            errors.append('Local da avaliação é obrigatório')
        
        if not terapias:
            errors.append('Pelo menos uma terapia deve ser recomendada')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('evaluations/form.html',
                                 patients=Patient.search(limit=100),
                                 specialties=get_specialties(),
                                 locations=get_locations(),
                                 available_therapies=Config.DEFAULT_SPECIALTIES,
                                 form_data=request.form)
        
        try:
            user_id = session.get('user_id')
            evaluation = Evaluation.create(
                paciente_id=paciente_id,
                medico_id=user_id,
                especialidade=especialidade,
                local=local,
                observacoes=observacoes,
                terapias=terapias,
                user_id=user_id
            )
            
            flash('Avaliação criada com sucesso!', 'success')
            return redirect(url_for('patients.detail', id=paciente_id))
            
        except Exception as e:
            flash(f'Erro ao criar avaliação: {str(e)}', 'error')
            return render_template('evaluations/form.html',
                                 patients=Patient.search(limit=100),
                                 specialties=get_specialties(),
                                 locations=get_locations(),
                                 available_therapies=Config.DEFAULT_SPECIALTIES,
                                 form_data=request.form)
    
    return render_template('evaluations/form.html',
                         patients=Patient.search(limit=100),
                         specialties=get_specialties(),
                         locations=get_locations(),
                         available_therapies=Config.DEFAULT_SPECIALTIES)

@evaluations_bp.route('/<int:id>')
@require_login
def detail(id):
    """Evaluation detail view"""
    evaluation = Evaluation.get_by_id(id)
    if not evaluation:
        flash('Avaliação não encontrada', 'error')
        return redirect(url_for('evaluations.list'))
    
    # Check permissions
    user_perfil = session.get('user_perfil')
    user_id = session.get('user_id')
    
    if user_perfil == 'medico' and evaluation.medico_id != user_id:
        flash('Acesso negado', 'error')
        return redirect(url_for('evaluations.list'))
    
    return render_template('evaluations/detail.html', evaluation=evaluation)
