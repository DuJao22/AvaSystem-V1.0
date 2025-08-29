# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.procedure import Procedure
from models.user import User
from utils.auth import require_login, require_permission
from utils.helpers import get_specialties

distribution_bp = Blueprint('distribution', __name__)

@distribution_bp.route('/')
@require_login
def center():
    """Distribution center view"""
    view_type = request.args.get('view', 'table')  # table or kanban
    
    # Build filters
    filters = {}
    
    if request.args.get('especialidade'):
        filters['especialidade'] = request.args.get('especialidade')
    
    if request.args.get('estado'):
        filters['estado'] = request.args.get('estado')
    
    user_perfil = session.get('user_perfil')
    user_id = session.get('user_id')
    
    # If doctor, can see option to filter by their procedures
    if user_perfil == 'medico' and request.args.get('meus_procedimentos') == '1':
        filters['medico_id'] = user_id
    
    procedures = Procedure.get_for_distribution(filters)
    
    # Group by specialty for kanban view
    procedures_by_specialty = {}
    if view_type == 'kanban':
        for procedure in procedures:
            if procedure.especialidade not in procedures_by_specialty:
                procedures_by_specialty[procedure.especialidade] = {
                    'pendente': [],
                    'alocado': [],
                    'em_atendimento': []
                }
            
            if procedure.estado in procedures_by_specialty[procedure.especialidade]:
                procedures_by_specialty[procedure.especialidade][procedure.estado].append(procedure)
    
    # Get filter options
    specialties = get_specialties()
    states = [
        ('pendente', 'Pendente'),
        ('alocado', 'Alocado'),
        ('em_atendimento', 'Em Atendimento')
    ]
    
    return render_template('distribution/center.html',
                         procedures=procedures,
                         procedures_by_specialty=procedures_by_specialty,
                         specialties=specialties,
                         states=states,
                         filters=filters,
                         view_type=view_type)

@distribution_bp.route('/puxar', methods=['POST'])
@require_login
@require_permission(['medico'])
def pull_patient():
    """Pull patient procedure to doctor"""
    procedure_id = request.form.get('procedure_id')
    
    if not procedure_id:
        flash('Procedimento não especificado', 'error')
        return redirect(url_for('distribution.center'))
    
    try:
        procedure_id = int(procedure_id)
        user_id = session.get('user_id')
        user_especialidade = session.get('user_especialidade')
        
        if not user_especialidade:
            flash('Especialidade do usuário não definida', 'error')
            return redirect(url_for('distribution.center'))
        
        procedure = Procedure.pull_to_doctor(
            procedure_id=procedure_id,
            medico_id=user_id,
            especialidade_medico=user_especialidade,
            user_id=user_id
        )
        
        if procedure and procedure.paciente_nome:
            flash(f'Paciente {procedure.paciente_nome} puxado com sucesso para {user_especialidade}!', 'success')
        else:
            flash(f'Paciente puxado com sucesso para {user_especialidade}!', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao puxar paciente: {str(e)}', 'error')
    
    return redirect(url_for('distribution.center'))

@distribution_bp.route('/devolver', methods=['POST'])
@require_login
def release_patient():
    """Release patient procedure from doctor"""
    procedure_id = request.form.get('procedure_id')
    motivo = request.form.get('motivo', '').strip()
    
    if not procedure_id:
        flash('Procedimento não especificado', 'error')
        return redirect(url_for('distribution.center'))
    
    if not motivo:
        flash('Motivo da devolução é obrigatório', 'error')
        return redirect(url_for('distribution.center'))
    
    try:
        procedure_id = int(procedure_id)
        user_id = session.get('user_id')
        user_perfil = session.get('user_perfil')
        
        # Check permissions
        procedure = Procedure.get_by_id(procedure_id)
        if not procedure:
            flash('Procedimento não encontrado', 'error')
            return redirect(url_for('distribution.center'))
        
        # Doctors can only release their own procedures
        # Coordination can release any procedure
        if user_perfil == 'medico' and procedure.medico_responsavel_id != user_id:
            flash('Você só pode devolver seus próprios procedimentos', 'error')
            return redirect(url_for('distribution.center'))
        
        procedure = Procedure.release_from_doctor(
            procedure_id=procedure_id,
            motivo=motivo,
            user_id=user_id
        )
        
        if procedure and procedure.paciente_nome:
            flash(f'Paciente {procedure.paciente_nome} devolvido com sucesso!', 'success')
        else:
            flash('Paciente devolvido com sucesso!', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao devolver paciente: {str(e)}', 'error')
    
    return redirect(url_for('distribution.center'))

@distribution_bp.route('/alterar-estado', methods=['POST'])
@require_login
@require_permission(['medico', 'coordenacao'])
def change_state():
    """Change procedure state"""
    procedure_id = request.form.get('procedure_id')
    new_state = request.form.get('new_state')
    
    if not procedure_id or not new_state:
        flash('Dados incompletos', 'error')
        return redirect(url_for('distribution.center'))
    
    try:
        procedure_id = int(procedure_id)
        user_id = session.get('user_id')
        user_perfil = session.get('user_perfil')
        
        # Check permissions
        procedure = Procedure.get_by_id(procedure_id)
        if not procedure:
            flash('Procedimento não encontrado', 'error')
            return redirect(url_for('distribution.center'))
        
        # Doctors can only change state of their own procedures
        if user_perfil == 'medico' and procedure.medico_responsavel_id != user_id:
            flash('Você só pode alterar o estado dos seus próprios procedimentos', 'error')
            return redirect(url_for('distribution.center'))
        
        procedure = Procedure.update_state(
            procedure_id=procedure_id,
            new_state=new_state,
            user_id=user_id
        )
        
        if procedure:
            flash(f'Estado do procedimento alterado para {procedure.get_state_display()}!', 'success')
        else:
            flash('Estado do procedimento alterado!', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao alterar estado: {str(e)}', 'error')
    
    return redirect(url_for('distribution.center'))
