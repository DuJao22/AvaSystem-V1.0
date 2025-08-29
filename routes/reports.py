# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session
from models.procedure import Procedure
from models.user import User
from utils.auth import require_login, require_permission
from utils.helpers import get_specialties
import csv
import io
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@require_login
def index():
    """Reports dashboard"""
    # Get statistics by specialty
    specialty_stats = Procedure.get_statistics_by_specialty()
    
    # Get statistics by doctor
    doctor_stats = Procedure.get_statistics_by_doctor()
    
    return render_template('reports/index.html',
                         specialty_stats=specialty_stats,
                         doctor_stats=doctor_stats)

@reports_bp.route('/especialidades')
@require_login
def specialties():
    """Specialty reports"""
    specialty_stats = Procedure.get_statistics_by_specialty()
    
    return render_template('reports/specialties.html',
                         specialty_stats=specialty_stats)

@reports_bp.route('/medicos')
@require_login
def doctors():
    """Doctor reports"""
    doctor_stats = Procedure.get_statistics_by_doctor()
    
    return render_template('reports/doctors.html',
                         doctor_stats=doctor_stats)

@reports_bp.route('/export/especialidades.csv')
@require_login
def export_specialties_csv():
    """Export specialty statistics to CSV"""
    specialty_stats = Procedure.get_statistics_by_specialty()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Especialidade', 'Pendente', 'Alocado', 'Em Atendimento', 'Concluído', 'Total'])
    
    # Data
    for specialty, stats in specialty_stats.items():
        writer.writerow([
            specialty,
            stats['pendente'],
            stats['alocado'],
            stats['em_atendimento'],
            stats['concluido'],
            stats['total']
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_especialidades.csv'
    
    return response

@reports_bp.route('/export/medicos.csv')
@require_login
def export_doctors_csv():
    """Export doctor statistics to CSV"""
    doctor_stats = Procedure.get_statistics_by_doctor()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Médico', 'Alocado', 'Em Atendimento', 'Concluído', 'Total'])
    
    # Data
    for doctor, stats in doctor_stats.items():
        writer.writerow([
            doctor,
            stats['alocado'],
            stats['em_atendimento'],
            stats['concluido'],
            stats['total']
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_medicos.csv'
    
    return response

@reports_bp.route('/export/procedimentos.csv')
@require_login
def export_procedures_csv():
    """Export all procedures to CSV"""
    procedures = Procedure.get_for_distribution()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Paciente', 'CPF', 'Especialidade', 'Estado', 
        'Médico Responsável', 'Criado em', 'Atualizado em', 'Motivo Devolução'
    ])
    
    # Data
    for procedure in procedures:
        writer.writerow([
            procedure.paciente_nome,
            procedure.paciente_cpf,
            procedure.especialidade,
            procedure.get_state_display(),
            procedure.medico_nome or '',
            procedure.criado_em,
            procedure.atualizado_em,
            procedure.motivo_devolucao or ''
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_procedimentos.csv'
    
    return response

@reports_bp.route('/distribuicao/imprimir')
@require_login
@require_permission(['admin'])
def distribution_print():
    """Generate printable A4 distribution report for admin"""
    # Get filters from query parameters
    filters = {}
    if request.args.get('especialidade'):
        filters['especialidade'] = request.args.get('especialidade')
    if request.args.get('estado'):
        filters['estado'] = request.args.get('estado')
    
    # Get procedures for the report
    procedures = Procedure.get_for_distribution(filters)
    
    # Get statistics by specialty
    specialty_stats = Procedure.get_statistics_by_specialty()
    
    # Filter specialty stats based on current filters
    if filters.get('especialidade'):
        specialty_stats = {
            filters['especialidade']: specialty_stats.get(filters['especialidade'], {
                'pendente': 0, 'alocado': 0, 'em_atendimento': 0, 'concluido': 0, 'total': 0
            })
        }
    
    # Get current user info for the report
    user_id = session.get('user_id')
    user_name = session.get('user_nome', 'Administrador')
    
    return render_template('reports/distribution_print.html',
                         procedures=procedures,
                         specialty_stats=specialty_stats,
                         filters=filters,
                         current_date=datetime.now(),
                         user_name=user_name)
