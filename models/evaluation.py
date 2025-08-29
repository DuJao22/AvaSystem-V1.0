# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from models.database import get_db_connection, get_db_transaction
from models.audit import log_action
from datetime import datetime

class Evaluation:
    """Evaluation model for managing clinical evaluations"""
    
    def __init__(self, id=None, paciente_id=None, medico_id=None, especialidade=None,
                 local=None, observacoes=None, criado_em=None, terapias=None):
        self.id = id
        self.paciente_id = paciente_id
        self.medico_id = medico_id
        self.especialidade = especialidade
        self.local = local
        self.observacoes = observacoes
        self.criado_em = criado_em
        self.terapias = terapias or []
    
    @classmethod
    def create(cls, paciente_id, medico_id, especialidade, local, observacoes, terapias, user_id=None):
        """Create a new evaluation with therapy recommendations"""
        with get_db_transaction() as conn:
            # Create evaluation
            cursor = conn.execute("""
                INSERT INTO avaliacoes (paciente_id, medico_id, especialidade, local, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (paciente_id, medico_id, especialidade, local, observacoes))
            
            evaluation_id = cursor.lastrowid
            
            # Add therapy recommendations
            for terapia in terapias:
                conn.execute("""
                    INSERT INTO avaliacao_terapias (avaliacao_id, terapia)
                    VALUES (?, ?)
                """, (evaluation_id, terapia))
                
                # Create or update procedure for this therapy
                cls._create_or_update_procedure(conn, paciente_id, terapia)
            
            # Log action
            patient_name = conn.execute("""
                SELECT nome FROM pacientes WHERE id = ?
            """, (paciente_id,)).fetchone()['nome']
            
            log_action(user_id, 'evaluation_created', 
                      f'Avaliação criada para {patient_name}. Terapias: {", ".join(terapias)}')
        
        return cls.get_by_id(evaluation_id)
    
    @classmethod
    def _create_or_update_procedure(cls, conn, paciente_id, especialidade):
        """Create or update procedure for patient and specialty"""
        # Check if procedure already exists
        existing = conn.execute("""
            SELECT id, estado FROM procedimentos 
            WHERE paciente_id = ? AND especialidade = ?
        """, (paciente_id, especialidade)).fetchone()
        
        if existing:
            # If procedure exists and is concluded, reset to pending
            if existing['estado'] == 'concluido':
                conn.execute("""
                    UPDATE procedimentos 
                    SET estado = 'pendente', medico_responsavel_id = NULL, 
                        motivo_devolucao = NULL, atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (existing['id'],))
        else:
            # Create new procedure
            conn.execute("""
                INSERT INTO procedimentos (paciente_id, especialidade, estado)
                VALUES (?, ?, 'pendente')
            """, (paciente_id, especialidade))
    
    @classmethod
    def get_by_id(cls, evaluation_id):
        """Get evaluation by ID with therapies"""
        conn = get_db_connection()
        
        # Get evaluation
        row = conn.execute("""
            SELECT a.*, u.nome as medico_nome, p.nome as paciente_nome
            FROM avaliacoes a
            JOIN users u ON a.medico_id = u.id
            JOIN pacientes p ON a.paciente_id = p.id
            WHERE a.id = ?
        """, (evaluation_id,)).fetchone()
        
        if not row:
            return None
        
        # Get therapies
        therapy_rows = conn.execute("""
            SELECT terapia FROM avaliacao_terapias WHERE avaliacao_id = ?
        """, (evaluation_id,)).fetchall()
        
        terapias = [t['terapia'] for t in therapy_rows]
        
        evaluation = cls(
            id=row['id'],
            paciente_id=row['paciente_id'],
            medico_id=row['medico_id'],
            especialidade=row['especialidade'],
            local=row['local'],
            observacoes=row['observacoes'],
            criado_em=row['criado_em'],
            terapias=terapias
        )
        
        # Add extra attributes for display
        evaluation.medico_nome = row['medico_nome']
        evaluation.paciente_nome = row['paciente_nome']
        
        return evaluation
    
    @classmethod
    def get_by_patient_id(cls, paciente_id):
        """Get all evaluations for a patient"""
        conn = get_db_connection()
        
        rows = conn.execute("""
            SELECT a.*, u.nome as medico_nome
            FROM avaliacoes a
            JOIN users u ON a.medico_id = u.id
            WHERE a.paciente_id = ?
            ORDER BY a.criado_em DESC
        """, (paciente_id,)).fetchall()
        
        evaluations = []
        for row in rows:
            # Get therapies for each evaluation
            therapy_rows = conn.execute("""
                SELECT terapia FROM avaliacao_terapias WHERE avaliacao_id = ?
            """, (row['id'],)).fetchall()
            
            terapias = [t['terapia'] for t in therapy_rows]
            
            evaluation = cls(
                id=row['id'],
                paciente_id=row['paciente_id'],
                medico_id=row['medico_id'],
                especialidade=row['especialidade'],
                local=row['local'],
                observacoes=row['observacoes'],
                criado_em=row['criado_em'],
                terapias=terapias
            )
            evaluation.medico_nome = row['medico_nome']
            evaluations.append(evaluation)
        
        return evaluations
    
    @classmethod
    def get_all(cls, filters=None, limit=50, offset=0):
        """Get all evaluations with optional filters"""
        conn = get_db_connection()
        
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('medico_id'):
                where_conditions.append("a.medico_id = ?")
                params.append(filters['medico_id'])
            
            if filters.get('especialidade'):
                where_conditions.append("a.especialidade = ?")
                params.append(filters['especialidade'])
            
            if filters.get('data_inicio'):
                where_conditions.append("DATE(a.criado_em) >= ?")
                params.append(filters['data_inicio'])
            
            if filters.get('data_fim'):
                where_conditions.append("DATE(a.criado_em) <= ?")
                params.append(filters['data_fim'])
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        params.extend([limit, offset])
        
        rows = conn.execute(f"""
            SELECT a.*, u.nome as medico_nome, p.nome as paciente_nome
            FROM avaliacoes a
            JOIN users u ON a.medico_id = u.id
            JOIN pacientes p ON a.paciente_id = p.id
            {where_clause}
            ORDER BY a.criado_em DESC
            LIMIT ? OFFSET ?
        """, params).fetchall()
        
        evaluations = []
        for row in rows:
            # Get therapies for each evaluation
            therapy_rows = conn.execute("""
                SELECT terapia FROM avaliacao_terapias WHERE avaliacao_id = ?
            """, (row['id'],)).fetchall()
            
            terapias = [t['terapia'] for t in therapy_rows]
            
            evaluation = cls(
                id=row['id'],
                paciente_id=row['paciente_id'],
                medico_id=row['medico_id'],
                especialidade=row['especialidade'],
                local=row['local'],
                observacoes=row['observacoes'],
                criado_em=row['criado_em'],
                terapias=terapias
            )
            evaluation.medico_nome = row['medico_nome']
            evaluation.paciente_nome = row['paciente_nome']
            evaluations.append(evaluation)
        
        return evaluations
    
    @classmethod
    def count_all(cls, filters=None):
        """Count evaluations with optional filters"""
        conn = get_db_connection()
        
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('medico_id'):
                where_conditions.append("medico_id = ?")
                params.append(filters['medico_id'])
            
            if filters.get('especialidade'):
                where_conditions.append("especialidade = ?")
                params.append(filters['especialidade'])
            
            if filters.get('data_inicio'):
                where_conditions.append("DATE(criado_em) >= ?")
                params.append(filters['data_inicio'])
            
            if filters.get('data_fim'):
                where_conditions.append("DATE(criado_em) <= ?")
                params.append(filters['data_fim'])
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        count = conn.execute(f"""
            SELECT COUNT(*) FROM avaliacoes {where_clause}
        """, params).fetchone()[0]
        
        return count
