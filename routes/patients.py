# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.patient import Patient
from models.evaluation import Evaluation
from models.procedure import Procedure
from utils.auth import require_login, require_permission
from utils.helpers import validate_date

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/')
@require_login
def list():
    """List patients with search and pagination"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    query = request.args.get('q', '').strip()
    patients = Patient.search(query, limit=per_page, offset=offset)
    
    # Get total count for pagination
    total = Patient.count_all()
    has_next = offset + per_page < total
    has_prev = page > 1
    
    return render_template('patients/list.html',
                         patients=patients,
                         query=query,
                         page=page,
                         has_next=has_next,
                         has_prev=has_prev)

@patients_bp.route('/novo', methods=['GET', 'POST'])
@require_login
@require_permission(['coordenacao', 'admin', 'medico'])
def new():
    """Create new patient"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        data_nascimento = request.form.get('data_nascimento', '').strip()
        telefone = request.form.get('telefone', '').strip()
        local_referencia = request.form.get('local_referencia', '').strip()
        
        # Validation
        errors = []
        
        if not nome:
            errors.append('Nome é obrigatório')
        
        if not cpf:
            errors.append('CPF é obrigatório')
        elif not Patient.validate_cpf(cpf):
            errors.append('CPF inválido')
        
        if not data_nascimento:
            errors.append('Data de nascimento é obrigatória')
        elif not validate_date(data_nascimento):
            errors.append('Data de nascimento inválida')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('patients/form.html',
                                 nome=nome, cpf=cpf, data_nascimento=data_nascimento,
                                 telefone=telefone, local_referencia=local_referencia)
        
        try:
            patient = Patient.create(
                nome=nome,
                cpf=cpf,
                data_nascimento=data_nascimento,
                telefone=telefone or None,
                local_referencia=local_referencia,
                user_id=session.get('user_id')
            )
            
            flash(f'Paciente {patient.nome} cadastrado com sucesso!', 'success')
            return redirect(url_for('patients.detail', id=patient.id))
            
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('patients/form.html',
                                 nome=nome, cpf=cpf, data_nascimento=data_nascimento,
                                 telefone=telefone, local_referencia=local_referencia)
    
    return render_template('patients/form.html')

@patients_bp.route('/<int:id>')
@require_login
def detail(id):
    """Patient detail view"""
    patient = Patient.get_by_id(id)
    if not patient:
        flash('Paciente não encontrado', 'error')
        return redirect(url_for('patients.list'))
    
    # Get patient's evaluations and procedures
    evaluations = patient.get_evaluations()
    procedures = patient.get_procedures()
    
    return render_template('patients/detail.html',
                         patient=patient,
                         evaluations=evaluations,
                         procedures=procedures)

@patients_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@require_login
@require_permission(['coordenacao', 'admin', 'medico'])
def edit(id):
    """Edit patient"""
    patient = Patient.get_by_id(id)
    if not patient:
        flash('Paciente não encontrado', 'error')
        return redirect(url_for('patients.list'))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        local_referencia = request.form.get('local_referencia', '').strip()
        
        # Validation
        if not nome:
            flash('Nome é obrigatório', 'error')
            return render_template('patients/form.html', 
                                 patient=patient, nome=nome, 
                                 telefone=telefone, local_referencia=local_referencia)
        
        try:
            patient.update(
                nome=nome,
                telefone=telefone or None,
                local_referencia=local_referencia,
                user_id=session.get('user_id')
            )
            
            flash(f'Paciente {patient.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('patients.detail', id=patient.id))
            
        except Exception as e:
            flash(f'Erro ao atualizar paciente: {str(e)}', 'error')
    
    return render_template('patients/form.html', patient=patient)
