# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_db_connection
from models.audit import log_action

class User:
    """User model with authentication and authorization"""
    
    def __init__(self, id=None, nome=None, email=None, perfil=None, especialidade=None, ativo=True, foto_perfil=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.perfil = perfil
        self.especialidade = especialidade
        self.ativo = ativo
        self.foto_perfil = foto_perfil
    
    @classmethod
    def create(cls, nome, email, senha, perfil, especialidade=None):
        """Create a new user"""
        conn = get_db_connection()
        senha_hash = generate_password_hash(senha)
        
        cursor = conn.execute("""
            INSERT INTO users (nome, email, senha_hash, perfil, especialidade)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, email, senha_hash, perfil, especialidade))
        
        conn.commit()
        
        user = cls.get_by_id(cursor.lastrowid)
        log_action(None, 'user_created', f'Usuário criado: {nome} ({email})')
        
        return user
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID"""
        conn = get_db_connection()
        row = conn.execute("""
            SELECT * FROM users WHERE id = ? AND ativo = 1
        """, (user_id,)).fetchone()
        
        if row:
            return cls(
                id=row['id'],
                nome=row['nome'],
                email=row['email'],
                perfil=row['perfil'],
                especialidade=row['especialidade'],
                ativo=row['ativo'],
                foto_perfil=row['foto_perfil'] if 'foto_perfil' in row.keys() else None
            )
        return None
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        conn = get_db_connection()
        row = conn.execute("""
            SELECT * FROM users WHERE email = ? AND ativo = 1
        """, (email,)).fetchone()
        
        if row:
            return cls(
                id=row['id'],
                nome=row['nome'],
                email=row['email'],
                perfil=row['perfil'],
                especialidade=row['especialidade'],
                ativo=row['ativo'],
                foto_perfil=row['foto_perfil'] if 'foto_perfil' in row.keys() else None
            )
        return None
    
    @classmethod
    def authenticate(cls, email, senha):
        """Authenticate user with email and password"""
        conn = get_db_connection()
        row = conn.execute("""
            SELECT * FROM users WHERE email = ? AND ativo = 1
        """, (email,)).fetchone()
        
        if row and check_password_hash(row['senha_hash'], senha):
            user = cls(
                id=row['id'],
                nome=row['nome'],
                email=row['email'],
                perfil=row['perfil'],
                especialidade=row['especialidade'],
                ativo=row['ativo'],
                foto_perfil=row['foto_perfil'] if 'foto_perfil' in row.keys() else None
            )
            log_action(user.id, 'login', f'Login realizado: {email}')
            return user
        
        log_action(None, 'login_failed', f'Tentativa de login falhada: {email}')
        return None
    
    @classmethod
    def get_all(cls):
        """Get all active users"""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT * FROM users WHERE ativo = 1 ORDER BY nome
        """).fetchall()
        
        return [cls(
            id=row['id'],
            nome=row['nome'],
            email=row['email'],
            perfil=row['perfil'],
            especialidade=row['especialidade'],
            ativo=row['ativo'],
            foto_perfil=row['foto_perfil'] if 'foto_perfil' in row.keys() else None
        ) for row in rows]
    
    @classmethod
    def get_doctors_by_specialty(cls, especialidade):
        """Get doctors by specialty"""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT * FROM users 
            WHERE perfil = 'medico' AND especialidade = ? AND ativo = 1
            ORDER BY nome
        """, (especialidade,)).fetchall()
        
        return [cls(
            id=row['id'],
            nome=row['nome'],
            email=row['email'],
            perfil=row['perfil'],
            especialidade=row['especialidade'],
            ativo=row['ativo'],
            foto_perfil=row['foto_perfil'] if 'foto_perfil' in row.keys() else None
        ) for row in rows]
    
    def update(self, nome=None, email=None, perfil=None, especialidade=None, foto_perfil=None):
        """Update user information"""
        conn = get_db_connection()
        
        if nome:
            self.nome = nome
        if email:
            self.email = email
        if perfil:
            self.perfil = perfil
        if especialidade is not None:
            self.especialidade = especialidade
        if foto_perfil is not None:
            self.foto_perfil = foto_perfil
        
        conn.execute("""
            UPDATE users 
            SET nome = ?, email = ?, perfil = ?, especialidade = ?, foto_perfil = ?
            WHERE id = ?
        """, (self.nome, self.email, self.perfil, self.especialidade, self.foto_perfil, self.id))
        
        conn.commit()
        log_action(self.id, 'user_updated', f'Usuário atualizado: {self.nome}')
    
    def deactivate(self):
        """Deactivate user"""
        conn = get_db_connection()
        conn.execute("UPDATE users SET ativo = 0 WHERE id = ?", (self.id,))
        conn.commit()
        
        self.ativo = False
        log_action(self.id, 'user_deactivated', f'Usuário desativado: {self.nome}')
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return self.ativo
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    def has_permission(self, action):
        """Check if user has permission for action"""
        permissions = {
            'admin': ['manage_users', 'manage_settings', 'view_all', 'manage_all'],
            'medico': ['create_evaluation', 'pull_patient', 'update_own_procedures', 'create_patient'],
            'coordenacao': ['create_patient', 'view_distribution', 'administrative_release']
        }
        
        return action in permissions.get(self.perfil or '', [])
    
    def change_password(self, current_password, new_password):
        """Change user password"""
        conn = get_db_connection()
        
        # Verify current password
        row = conn.execute("""
            SELECT senha_hash FROM users WHERE id = ?
        """, (self.id,)).fetchone()
        
        if not row or not check_password_hash(row['senha_hash'], current_password):
            return False, 'Senha atual incorreta'
        
        # Update password
        new_hash = generate_password_hash(new_password)
        conn.execute("""
            UPDATE users SET senha_hash = ? WHERE id = ?
        """, (new_hash, self.id))
        
        conn.commit()
        log_action(self.id, 'password_changed', f'Senha alterada para usuário: {self.nome}')
        
        return True, 'Senha alterada com sucesso'
    
    def update_profile(self, nome=None, foto_perfil=None):
        """Update user profile (nome e foto)"""
        conn = get_db_connection()
        
        if nome:
            self.nome = nome
        if foto_perfil is not None:
            self.foto_perfil = foto_perfil
        
        conn.execute("""
            UPDATE users 
            SET nome = ?, foto_perfil = ?
            WHERE id = ?
        """, (self.nome, self.foto_perfil, self.id))
        
        conn.commit()
        log_action(self.id, 'profile_updated', f'Perfil atualizado: {self.nome}')
        
        return True, 'Perfil atualizado com sucesso'
