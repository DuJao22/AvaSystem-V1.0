# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from models.database import get_db_connection, get_db_transaction
from models.audit import log_action

class Procedure:
    """Procedure model for managing therapy procedures"""
    
    def __init__(self, id=None, paciente_id=None, especialidade=None, estado=None,
                 medico_responsavel_id=None, motivo_devolucao=None, 
                 criado_em=None, atualizado_em=None):
        self.id = id
        self.paciente_id = paciente_id
        self.especialidade = especialidade
        self.estado = estado
        self.medico_responsavel_id = medico_responsavel_id
        self.motivo_devolucao = motivo_devolucao
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em
        # Dynamic attributes for joined data
        self.paciente_nome = None
        self.paciente_cpf = None
        self.medico_nome = None
    
    @classmethod
    def get_by_id(cls, procedure_id):
        """Get procedure by ID"""
        conn = get_db_connection()
        row = conn.execute("""
            SELECT p.*, pac.nome as paciente_nome, u.nome as medico_nome
            FROM procedimentos p
            JOIN pacientes pac ON p.paciente_id = pac.id
            LEFT JOIN users u ON p.medico_responsavel_id = u.id
            WHERE p.id = ?
        """, (procedure_id,)).fetchone()
        
        if row:
            procedure = cls(
                id=row['id'],
                paciente_id=row['paciente_id'],
                especialidade=row['especialidade'],
                estado=row['estado'],
                medico_responsavel_id=row['medico_responsavel_id'],
                motivo_devolucao=row['motivo_devolucao'],
                criado_em=row['criado_em'],
                atualizado_em=row['atualizado_em']
            )
            procedure.paciente_nome = row['paciente_nome']
            procedure.medico_nome = row['medico_nome']
            return procedure
        return None
    
    @classmethod
    def get_by_patient_id(cls, paciente_id):
        """Get all procedures for a patient"""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT p.*, u.nome as medico_nome
            FROM procedimentos p
            LEFT JOIN users u ON p.medico_responsavel_id = u.id
            WHERE p.paciente_id = ?
            ORDER BY p.especialidade, p.atualizado_em DESC
        """, (paciente_id,)).fetchall()
        
        procedures = []
        for row in rows:
            procedure = cls(
                id=row['id'],
                paciente_id=row['paciente_id'],
                especialidade=row['especialidade'],
                estado=row['estado'],
                medico_responsavel_id=row['medico_responsavel_id'],
                motivo_devolucao=row['motivo_devolucao'],
                criado_em=row['criado_em'],
                atualizado_em=row['atualizado_em']
            )
            procedure.medico_nome = row['medico_nome']
            procedures.append(procedure)
        
        return procedures
    
    @classmethod
    def get_for_distribution(cls, filters=None):
        """Get procedures for distribution center"""
        conn = get_db_connection()
        
        where_conditions = ["p.estado != 'concluido'"]
        params = []
        
        if filters:
            if filters.get('especialidade'):
                where_conditions.append("p.especialidade = ?")
                params.append(filters['especialidade'])
            
            if filters.get('estado'):
                where_conditions.append("p.estado = ?")
                params.append(filters['estado'])
            
            if filters.get('medico_id'):
                where_conditions.append("p.medico_responsavel_id = ?")
                params.append(filters['medico_id'])
        
        where_clause = " AND ".join(where_conditions)
        
        rows = conn.execute(f"""
            SELECT p.*, pac.nome as paciente_nome, pac.cpf as paciente_cpf,
                   u.nome as medico_nome
            FROM procedimentos p
            JOIN pacientes pac ON p.paciente_id = pac.id
            LEFT JOIN users u ON p.medico_responsavel_id = u.id
            WHERE {where_clause}
            ORDER BY p.especialidade, p.estado, p.atualizado_em
        """, params).fetchall()
        
        procedures = []
        for row in rows:
            procedure = cls(
                id=row['id'],
                paciente_id=row['paciente_id'],
                especialidade=row['especialidade'],
                estado=row['estado'],
                medico_responsavel_id=row['medico_responsavel_id'],
                motivo_devolucao=row['motivo_devolucao'],
                criado_em=row['criado_em'],
                atualizado_em=row['atualizado_em']
            )
            procedure.paciente_nome = row['paciente_nome']
            procedure.paciente_cpf = row['paciente_cpf']
            procedure.medico_nome = row['medico_nome']
            procedures.append(procedure)
        
        return procedures
    
    @classmethod
    def pull_to_doctor(cls, procedure_id, medico_id, especialidade_medico, user_id=None):
        """Pull procedure to doctor with exclusive locking"""
        with get_db_transaction() as conn:
            # Check if procedure exists and is available
            procedure_row = conn.execute("""
                SELECT p.*, pac.nome as paciente_nome
                FROM procedimentos p
                JOIN pacientes pac ON p.paciente_id = pac.id
                WHERE p.id = ?
            """, (procedure_id,)).fetchone()
            
            if not procedure_row:
                raise ValueError("Procedimento não encontrado")
            
            if procedure_row['estado'] not in ['pendente']:
                raise ValueError("Procedimento não está disponível para alocação")
            
            # Check if doctor specialty matches procedure
            if procedure_row['especialidade'] != especialidade_medico:
                raise ValueError("Especialidade do médico não corresponde ao procedimento")
            
            # Check for existing allocation to same specialty
            existing = conn.execute("""
                SELECT id FROM procedimentos 
                WHERE paciente_id = ? AND especialidade = ? 
                AND estado IN ('alocado', 'em_atendimento')
            """, (procedure_row['paciente_id'], especialidade_medico)).fetchone()
            
            if existing and existing['id'] != procedure_id:
                raise ValueError("Paciente já alocado para outro médico desta especialidade")
            
            # Allocate procedure to doctor
            conn.execute("""
                UPDATE procedimentos 
                SET estado = 'alocado', medico_responsavel_id = ?, 
                    motivo_devolucao = NULL, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (medico_id, procedure_id))
            
            # Log action
            log_action(user_id, 'procedure_pulled', 
                      f'Procedimento puxado: {procedure_row["paciente_nome"]} - {especialidade_medico}')
        
        return cls.get_by_id(procedure_id)
    
    @classmethod
    def release_from_doctor(cls, procedure_id, motivo, user_id=None):
        """Release procedure from doctor"""
        with get_db_transaction() as conn:
            # Get procedure info
            procedure_row = conn.execute("""
                SELECT p.*, pac.nome as paciente_nome
                FROM procedimentos p
                JOIN pacientes pac ON p.paciente_id = pac.id
                WHERE p.id = ?
            """, (procedure_id,)).fetchone()
            
            if not procedure_row:
                raise ValueError("Procedimento não encontrado")
            
            if procedure_row['estado'] not in ['alocado', 'em_atendimento']:
                raise ValueError("Procedimento não está alocado")
            
            # Release procedure
            conn.execute("""
                UPDATE procedimentos 
                SET estado = 'pendente', medico_responsavel_id = NULL, 
                    motivo_devolucao = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (motivo, procedure_id))
            
            # Log action
            log_action(user_id, 'procedure_released', 
                      f'Procedimento liberado: {procedure_row["paciente_nome"]} - {procedure_row["especialidade"]}. Motivo: {motivo}')
        
        return cls.get_by_id(procedure_id)
    
    @classmethod
    def update_state(cls, procedure_id, new_state, user_id=None):
        """Update procedure state"""
        valid_states = ['pendente', 'alocado', 'em_atendimento', 'concluido']
        if new_state not in valid_states:
            raise ValueError("Estado inválido")
        
        with get_db_transaction() as conn:
            # Get procedure info
            procedure_row = conn.execute("""
                SELECT p.*, pac.nome as paciente_nome
                FROM procedimentos p
                JOIN pacientes pac ON p.paciente_id = pac.id
                WHERE p.id = ?
            """, (procedure_id,)).fetchone()
            
            if not procedure_row:
                raise ValueError("Procedimento não encontrado")
            
            # Update state
            conn.execute("""
                UPDATE procedimentos 
                SET estado = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_state, procedure_id))
            
            # Log action
            log_action(user_id, 'procedure_state_updated', 
                      f'Estado do procedimento alterado: {procedure_row["paciente_nome"]} - {procedure_row["especialidade"]} para {new_state}')
        
        return cls.get_by_id(procedure_id)
    
    @classmethod
    def get_statistics_by_specialty(cls):
        """Get procedure statistics by specialty"""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT especialidade, estado, COUNT(*) as count
            FROM procedimentos
            GROUP BY especialidade, estado
            ORDER BY especialidade, estado
        """).fetchall()
        
        stats = {}
        for row in rows:
            if row['especialidade'] not in stats:
                stats[row['especialidade']] = {
                    'pendente': 0,
                    'alocado': 0,
                    'em_atendimento': 0,
                    'concluido': 0,
                    'total': 0
                }
            
            stats[row['especialidade']][row['estado']] = row['count']
            stats[row['especialidade']]['total'] += row['count']
        
        return stats
    
    @classmethod
    def get_statistics_by_doctor(cls):
        """Get procedure statistics by doctor"""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT u.nome as medico_nome, u.especialidade, p.estado, COUNT(*) as count
            FROM procedimentos p
            JOIN users u ON p.medico_responsavel_id = u.id
            WHERE p.medico_responsavel_id IS NOT NULL
            GROUP BY u.id, u.nome, u.especialidade, p.estado
            ORDER BY u.nome, p.estado
        """).fetchall()
        
        stats = {}
        for row in rows:
            key = f"{row['medico_nome']} ({row['especialidade']})"
            if key not in stats:
                stats[key] = {
                    'alocado': 0,
                    'em_atendimento': 0,
                    'concluido': 0,
                    'total': 0
                }
            
            if row['estado'] in stats[key]:
                stats[key][row['estado']] = row['count']
                stats[key]['total'] += row['count']
        
        return stats
    
    def get_state_badge_class(self):
        """Get CSS class for state badge"""
        classes = {
            'pendente': 'bg-yellow-100 text-yellow-800',
            'alocado': 'bg-blue-100 text-blue-800',
            'em_atendimento': 'bg-purple-100 text-purple-800',
            'concluido': 'bg-green-100 text-green-800'
        }
        return classes.get(self.estado or '', 'bg-gray-100 text-gray-800')
    
    def get_state_display(self):
        """Get display text for state"""
        states = {
            'pendente': 'Pendente',
            'alocado': 'Alocado',
            'em_atendimento': 'Em Atendimento',
            'concluido': 'Concluído'
        }
        return states.get(self.estado or '', self.estado or 'Desconhecido')
