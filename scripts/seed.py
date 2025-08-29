#!/usr/bin/env python3
# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

"""
Database seeding script
Populates the database with sample data for testing and demonstration
"""

import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user import User
from models.patient import Patient
from models.evaluation import Evaluation
from models.procedure import Procedure
from models.audit import log_action
from config import Config

def seed_database():
    """Seed the database with sample data"""
    
    print("Populando banco de dados com dados de demonstração...")
    
    try:
        # Create users
        print("Criando usuários...")
        create_users()
        
        # Create patients
        print("Criando pacientes...")
        create_patients()
        
        # Create evaluations
        print("Criando avaliações...")
        create_evaluations()
        
        # Update some procedures to show different states
        print("Atualizando estados dos procedimentos...")
        update_procedure_states()
        
        print("\n" + "="*50)
        print("DADOS DE DEMONSTRAÇÃO CRIADOS COM SUCESSO!")
        print("="*50)
        print("Usuários criados:")
        print("- admin@sistema.com (senha: admin123) - Administrador")
        print("- fono@clinica.com (senha: fono123) - Fonoaudióloga")
        print("- psi@clinica.com (senha: psi123) - Psicóloga")
        print("- to@clinica.com (senha: to123) - Terapeuta Ocupacional")
        print("- coord@clinica.com (senha: coord123) - Coordenação")
        print("="*50)
        print("Para iniciar o sistema, execute:")
        print("python app.py")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Erro ao popular banco de dados: {str(e)}")
        sys.exit(1)

def create_users():
    """Create sample users"""
    users_data = [
        {
            'nome': 'Administrador do Sistema',
            'email': 'admin@sistema.com',
            'senha': 'admin123',
            'perfil': 'admin',
            'especialidade': None
        },
        {
            'nome': 'Dra. Maria Silva',
            'email': 'fono@clinica.com',
            'senha': 'fono123',
            'perfil': 'medico',
            'especialidade': 'Fonoaudiologia'
        },
        {
            'nome': 'Dr. João Santos',
            'email': 'psi@clinica.com',
            'senha': 'psi123',
            'perfil': 'medico',
            'especialidade': 'Psicologia'
        },
        {
            'nome': 'Dra. Ana Costa',
            'email': 'to@clinica.com',
            'senha': 'to123',
            'perfil': 'medico',
            'especialidade': 'Terapia Ocupacional'
        },
        {
            'nome': 'Coordenação Clínica',
            'email': 'coord@clinica.com',
            'senha': 'coord123',
            'perfil': 'coordenacao',
            'especialidade': None
        }
    ]
    
    for user_data in users_data:
        try:
            existing_user = User.get_by_email(user_data['email'])
            if not existing_user:
                User.create(**user_data)
                print(f"✓ Usuário criado: {user_data['nome']} ({user_data['email']})")
            else:
                print(f"- Usuário já existe: {user_data['email']}")
        except Exception as e:
            print(f"❌ Erro ao criar usuário {user_data['email']}: {str(e)}")

def create_patients():
    """Create sample patients"""
    patients_data = [
        {
            'nome': 'João Pedro Silva',
            'cpf': '12345678901',
            'data_nascimento': '2015-03-15',
            'telefone': '(11) 99999-1234',
            'local_referencia': 'Clínica Principal'
        },
        {
            'nome': 'Maria Eduarda Santos',
            'cpf': '23456789012',
            'data_nascimento': '2016-07-22',
            'telefone': '(11) 99999-2345',
            'local_referencia': 'Unidade Norte'
        },
        {
            'nome': 'Pedro Henrique Costa',
            'cpf': '34567890123',
            'data_nascimento': '2014-11-08',
            'telefone': '(11) 99999-3456',
            'local_referencia': 'Clínica Principal'
        },
        {
            'nome': 'Ana Clara Oliveira',
            'cpf': '45678901234',
            'data_nascimento': '2017-01-30',
            'telefone': '(11) 99999-4567',
            'local_referencia': 'Unidade Sul'
        },
        {
            'nome': 'Gabriel Ferreira',
            'cpf': '56789012345',
            'data_nascimento': '2013-09-12',
            'telefone': '(11) 99999-5678',
            'local_referencia': 'Clínica Principal'
        },
        {
            'nome': 'Isabela Rodrigues',
            'cpf': '67890123456',
            'data_nascimento': '2018-04-05',
            'telefone': '(11) 99999-6789',
            'local_referencia': 'Atendimento Domiciliar'
        },
        {
            'nome': 'Lucas Almeida',
            'cpf': '78901234567',
            'data_nascimento': '2015-12-18',
            'telefone': '(11) 99999-7890',
            'local_referencia': 'Unidade Norte'
        },
        {
            'nome': 'Sophia Lima',
            'cpf': '89012345678',
            'data_nascimento': '2016-08-25',
            'telefone': '(11) 99999-8901',
            'local_referencia': 'Clínica Principal'
        },
        {
            'nome': 'Miguel Barbosa',
            'cpf': '90123456789',
            'data_nascimento': '2014-06-14',
            'telefone': '(11) 99999-9012',
            'local_referencia': 'Unidade Sul'
        },
        {
            'nome': 'Valentina Pereira',
            'cpf': '01234567890',
            'data_nascimento': '2017-10-03',
            'telefone': '(11) 99999-0123',
            'local_referencia': 'Clínica Principal'
        }
    ]
    
    admin_user = User.get_by_email('admin@sistema.com')
    admin_id = admin_user.id if admin_user else None
    
    for patient_data in patients_data:
        try:
            existing_patient = Patient.get_by_cpf(patient_data['cpf'])
            if not existing_patient:
                Patient.create(user_id=admin_id, **patient_data)
                print(f"✓ Paciente criado: {patient_data['nome']}")
            else:
                print(f"- Paciente já existe: {patient_data['nome']}")
        except Exception as e:
            print(f"❌ Erro ao criar paciente {patient_data['nome']}: {str(e)}")

def create_evaluations():
    """Create sample evaluations"""
    # Get users and patients
    fono_user = User.get_by_email('fono@clinica.com')
    psi_user = User.get_by_email('psi@clinica.com')
    to_user = User.get_by_email('to@clinica.com')
    
    if not all([fono_user, psi_user, to_user]):
        print("❌ Usuários médicos não encontrados")
        return
    
    patients = Patient.search(limit=10)
    if not patients:
        print("❌ Nenhum paciente encontrado")
        return
    
    # Sample evaluations data
    evaluations_data = [
        {
            'medico': fono_user,
            'especialidade': 'Fonoaudiologia',
            'local': 'Clínica Principal',
            'observacoes': 'Paciente apresenta atraso na fala. Recomendado acompanhamento intensivo.',
            'terapias': ['Fonoaudiologia', 'Psicologia']
        },
        {
            'medico': psi_user,
            'especialidade': 'Psicologia',
            'local': 'Unidade Norte',
            'observacoes': 'Avaliação psicológica indica necessidade de intervenção comportamental.',
            'terapias': ['Psicologia', 'Terapia Ocupacional', 'Pedagogia/ABA']
        },
        {
            'medico': to_user,
            'especialidade': 'Terapia Ocupacional',
            'local': 'Clínica Principal',
            'observacoes': 'Dificuldades de coordenação motora e integração sensorial.',
            'terapias': ['Terapia Ocupacional', 'Fisioterapia']
        },
        {
            'medico': fono_user,
            'especialidade': 'Fonoaudiologia',
            'local': 'Unidade Sul',
            'observacoes': 'Boa evolução na comunicação. Manutenção do tratamento recomendada.',
            'terapias': ['Fonoaudiologia', 'Musicoterapia']
        },
        {
            'medico': psi_user,
            'especialidade': 'Psicologia',
            'local': 'Atendimento Domiciliar',
            'observacoes': 'Primeira avaliação. Paciente com sinais de TEA. Intervenção multidisciplinar necessária.',
            'terapias': ['Psicologia', 'Fonoaudiologia', 'Terapia Ocupacional', 'Pedagogia/ABA']
        }
    ]
    
    # Create evaluations for random patients
    for i, eval_data in enumerate(evaluations_data):
        try:
            if i < len(patients):
                patient = patients[i]
                
                Evaluation.create(
                    paciente_id=patient.id,
                    medico_id=eval_data['medico'].id,
                    especialidade=eval_data['especialidade'],
                    local=eval_data['local'],
                    observacoes=eval_data['observacoes'],
                    terapias=eval_data['terapias'],
                    user_id=eval_data['medico'].id
                )
                print(f"✓ Avaliação criada: {patient.nome} - {eval_data['especialidade']}")
        except Exception as e:
            print(f"❌ Erro ao criar avaliação: {str(e)}")
    
    # Create additional evaluations for variety
    additional_evaluations = [
        (6, fono_user, 'Fonoaudiologia', ['Fonoaudiologia']),
        (7, psi_user, 'Psicologia', ['Psicologia', 'Musicoterapia']),
        (8, to_user, 'Terapia Ocupacional', ['Terapia Ocupacional', 'Fisioterapia']),
        (9, fono_user, 'Fonoaudiologia', ['Fonoaudiologia', 'Psicologia', 'Terapia Ocupacional'])
    ]
    
    for patient_idx, medico, especialidade, terapias in additional_evaluations:
        try:
            if patient_idx < len(patients):
                patient = patients[patient_idx]
                
                Evaluation.create(
                    paciente_id=patient.id,
                    medico_id=medico.id,
                    especialidade=especialidade,
                    local=random.choice(['Clínica Principal', 'Unidade Norte', 'Unidade Sul']),
                    observacoes=f'Avaliação de {especialidade} realizada. Paciente em acompanhamento.',
                    terapias=terapias,
                    user_id=medico.id
                )
                print(f"✓ Avaliação adicional criada: {patient.nome} - {especialidade}")
        except Exception as e:
            print(f"❌ Erro ao criar avaliação adicional: {str(e)}")

def update_procedure_states():
    """Update some procedures to show different states"""
    try:
        # Get some procedures to update
        procedures = Procedure.get_for_distribution()
        
        if not procedures:
            print("- Nenhum procedimento encontrado para atualizar")
            return
        
        # Get users for allocating procedures
        fono_user = User.get_by_email('fono@clinica.com')
        psi_user = User.get_by_email('psi@clinica.com')
        to_user = User.get_by_email('to@clinica.com')
        
        # Allocate some procedures
        allocated_count = 0
        in_treatment_count = 0
        completed_count = 0
        
        for procedure in procedures[:8]:  # Work with first 8 procedures
            try:
                # Determine which doctor can handle this procedure
                doctor = None
                if procedure.especialidade == 'Fonoaudiologia' and fono_user:
                    doctor = fono_user
                elif procedure.especialidade == 'Psicologia' and psi_user:
                    doctor = psi_user
                elif procedure.especialidade == 'Terapia Ocupacional' and to_user:
                    doctor = to_user
                
                if doctor and allocated_count < 3:
                    # Allocate procedure
                    Procedure.pull_to_doctor(
                        procedure_id=procedure.id,
                        medico_id=doctor.id,
                        especialidade_medico=doctor.especialidade,
                        user_id=doctor.id
                    )
                    allocated_count += 1
                    print(f"✓ Procedimento alocado: {procedure.paciente_nome} - {procedure.especialidade}")
                    
                elif doctor and in_treatment_count < 2:
                    # Allocate and move to in treatment
                    Procedure.pull_to_doctor(
                        procedure_id=procedure.id,
                        medico_id=doctor.id,
                        especialidade_medico=doctor.especialidade,
                        user_id=doctor.id
                    )
                    Procedure.update_state(
                        procedure_id=procedure.id,
                        new_state='em_atendimento',
                        user_id=doctor.id
                    )
                    in_treatment_count += 1
                    print(f"✓ Procedimento em atendimento: {procedure.paciente_nome} - {procedure.especialidade}")
                    
                elif doctor and completed_count < 1:
                    # Allocate, move to in treatment, then complete
                    Procedure.pull_to_doctor(
                        procedure_id=procedure.id,
                        medico_id=doctor.id,
                        especialidade_medico=doctor.especialidade,
                        user_id=doctor.id
                    )
                    Procedure.update_state(
                        procedure_id=procedure.id,
                        new_state='em_atendimento',
                        user_id=doctor.id
                    )
                    Procedure.update_state(
                        procedure_id=procedure.id,
                        new_state='concluido',
                        user_id=doctor.id
                    )
                    completed_count += 1
                    print(f"✓ Procedimento concluído: {procedure.paciente_nome} - {procedure.especialidade}")
                    
            except Exception as e:
                print(f"⚠ Erro ao atualizar procedimento {procedure.id}: {str(e)}")
                continue
        
        print(f"✓ Estados atualizados: {allocated_count} alocados, {in_treatment_count} em atendimento, {completed_count} concluídos")
        
    except Exception as e:
        print(f"❌ Erro ao atualizar estados dos procedimentos: {str(e)}")

if __name__ == "__main__":
    seed_database()
