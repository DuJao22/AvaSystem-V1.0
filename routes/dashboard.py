# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from flask import Blueprint, render_template, session, redirect, url_for
from models.patient import Patient
from models.evaluation import Evaluation
from models.procedure import Procedure
from utils.auth import require_login

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@require_login
def index():
    """Main dashboard with metrics"""
    user_perfil = session.get('user_perfil')
    user_id = session.get('user_id')
    
    # Get basic statistics
    total_patients = Patient.count_all()
    
    # Get procedure statistics by specialty
    specialty_stats = Procedure.get_statistics_by_specialty()
    
    # Calculate totals
    total_procedures = sum(stats['total'] for stats in specialty_stats.values())
    total_pending = sum(stats['pendente'] for stats in specialty_stats.values())
    total_allocated = sum(stats['alocado'] for stats in specialty_stats.values())
    total_in_treatment = sum(stats['em_atendimento'] for stats in specialty_stats.values())
    total_completed = sum(stats['concluido'] for stats in specialty_stats.values())
    
    # Get recent evaluations (last 7 days)
    from datetime import datetime, timedelta
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_evaluations = Evaluation.count_all({'data_inicio': week_ago})
    
    # User-specific statistics
    user_stats = None
    if user_perfil == 'medico':
        # Get doctor's current procedures
        doctor_procedures = Procedure.get_for_distribution({'medico_id': user_id})
        user_stats = {
            'meus_alocados': len([p for p in doctor_procedures if p.estado == 'alocado']),
            'meus_em_atendimento': len([p for p in doctor_procedures if p.estado == 'em_atendimento']),
            'meus_concluidos': len([p for p in doctor_procedures if p.estado == 'concluido'])
        }
    
    return render_template('dashboard.html', 
                         total_patients=total_patients,
                         total_procedures=total_procedures,
                         total_pending=total_pending,
                         total_allocated=total_allocated,
                         total_in_treatment=total_in_treatment,
                         total_completed=total_completed,
                         recent_evaluations=recent_evaluations,
                         specialty_stats=specialty_stats,
                         user_stats=user_stats)
