# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from models.database import get_db_connection
from models.audit import log_action
import re

class Patient:
    """Patient model for managing patient data"""
    
    def __init__(self, id=None, nome=None, cpf=None, data_nascimento=None, 
                 telefone=None, local_referencia=None, criado_em=None):
        self.id = id
        self.nome = nome
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.telefone = telefone
        self.local_referencia = local_referencia
        self.criado_em = criado_em
    
    @staticmethod
    def validate_cpf(cpf):
        """Validate CPF format and checksum"""
        if not cpf:
            return False
        
        # Remove non-digits
        cpf = re.sub(r'\D', '', cpf)
        
        if len(cpf) != 11:
            return False
        
        # Check for known invalid patterns
        if cpf in ['00000000000', '11111111111', '22222222222', 
                   '33333333333', '44444444444', '55555555555',
                   '66666666666', '77777777777', '88888888888', '99999999999']:
            return False
        
        # Validate checksum
        def calculate_digit(cpf_partial):
            total = sum(int(cpf_partial[i]) * (len(cpf_partial) + 1 - i) 
                       for i in range(len(cpf_partial)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_digit = calculate_digit(cpf[:9])
        second_digit = calculate_digit(cpf[:10])
        
        return cpf[9] == str(first_digit) and cpf[10] == str(second_digit)
    
    @classmethod
    def create(cls, nome, cpf, data_nascimento, telefone=None, local_referencia=None, user_id=None):
        """Create a new patient"""
        if not cls.validate_cpf(cpf):
            raise ValueError("CPF inválido")
        
        # Clean CPF
        clean_cpf = re.sub(r'\D', '', cpf)
        
        conn = get_db_connection()
        
        # Check if CPF already exists
        existing = conn.execute("""
            SELECT id FROM pacientes WHERE cpf = ?
        """, (clean_cpf,)).fetchone()
        
        if existing:
            raise ValueError("CPF já cadastrado no sistema")
        
        cursor = conn.execute("""
            INSERT INTO pacientes (nome, cpf, data_nascimento, telefone, local_referencia)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, clean_cpf, data_nascimento, telefone, local_referencia))
        
        conn.commit()
        
        patient = cls.get_by_id(cursor.lastrowid)
        log_action(user_id, 'patient_created', f'Paciente cadastrado: {nome} (CPF: {clean_cpf})')
        
        return patient
    
    @classmethod
    def get_by_id(cls, patient_id):
        """Get patient by ID"""
        conn = get_db_connection()
        row = conn.execute("""
            SELECT * FROM pacientes WHERE id = ?
        """, (patient_id,)).fetchone()
        
        if row:
            return cls(
                id=row['id'],
                nome=row['nome'],
                cpf=row['cpf'],
                data_nascimento=row['data_nascimento'],
                telefone=row['telefone'],
                local_referencia=row['local_referencia'],
                criado_em=row['criado_em']
            )
        return None
    
    @classmethod
    def get_by_cpf(cls, cpf):
        """Get patient by CPF"""
        clean_cpf = re.sub(r'\D', '', cpf)
        conn = get_db_connection()
        row = conn.execute("""
            SELECT * FROM pacientes WHERE cpf = ?
        """, (clean_cpf,)).fetchone()
        
        if row:
            return cls(
                id=row['id'],
                nome=row['nome'],
                cpf=row['cpf'],
                data_nascimento=row['data_nascimento'],
                telefone=row['telefone'],
                local_referencia=row['local_referencia'],
                criado_em=row['criado_em']
            )
        return None
    
    @classmethod
    def search(cls, query=None, limit=50, offset=0):
        """Search patients by name, CPF, or phone"""
        conn = get_db_connection()
        
        if query:
            clean_query = re.sub(r'\D', '', query) if query.replace(' ', '').isdigit() else query
            rows = conn.execute("""
                SELECT * FROM pacientes 
                WHERE nome LIKE ? OR cpf LIKE ? OR telefone LIKE ?
                ORDER BY nome
                LIMIT ? OFFSET ?
            """, (f"%{query}%", f"%{clean_query}%", f"%{query}%", limit, offset)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM pacientes 
                ORDER BY nome
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
        
        return [cls(
            id=row['id'],
            nome=row['nome'],
            cpf=row['cpf'],
            data_nascimento=row['data_nascimento'],
            telefone=row['telefone'],
            local_referencia=row['local_referencia'],
            criado_em=row['criado_em']
        ) for row in rows]
    
    @classmethod
    def count_all(cls):
        """Count all patients"""
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
        return count
    
    def update(self, nome=None, telefone=None, local_referencia=None, user_id=None):
        """Update patient information"""
        conn = get_db_connection()
        
        if nome:
            self.nome = nome
        if telefone is not None:
            self.telefone = telefone
        if local_referencia:
            self.local_referencia = local_referencia
        
        conn.execute("""
            UPDATE pacientes 
            SET nome = ?, telefone = ?, local_referencia = ?
            WHERE id = ?
        """, (self.nome, self.telefone, self.local_referencia, self.id))
        
        conn.commit()
        log_action(user_id, 'patient_updated', f'Paciente atualizado: {self.nome}')
    
    def get_evaluations(self):
        """Get all evaluations for this patient"""
        from models.evaluation import Evaluation
        return Evaluation.get_by_patient_id(self.id)
    
    def get_procedures(self):
        """Get all procedures for this patient"""
        from models.procedure import Procedure
        return Procedure.get_by_patient_id(self.id)
    
    def format_cpf(self):
        """Format CPF for display"""
        if self.cpf and len(self.cpf) == 11:
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return self.cpf
    
    def format_phone(self):
        """Format phone for display"""
        if self.telefone:
            clean_phone = re.sub(r'\D', '', self.telefone)
            if len(clean_phone) == 11:
                return f"({clean_phone[:2]}) {clean_phone[2:7]}-{clean_phone[7:]}"
            elif len(clean_phone) == 10:
                return f"({clean_phone[:2]}) {clean_phone[2:6]}-{clean_phone[6:]}"
        return self.telefone
