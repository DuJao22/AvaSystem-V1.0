# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

import sqlite3
import os
from contextlib import contextmanager
from threading import local
try:
    import sqlitecloud
    SQLITECLOUD_AVAILABLE = True
except ImportError:
    SQLITECLOUD_AVAILABLE = False

# Thread-local storage for database connections
_local = local()

def get_db_connection(db_url=None):
    """Get database connection for current thread"""
    if not hasattr(_local, 'connection') or _local.connection is None:
        db_path = db_url or 'instance/app.db'
        
        # Check if using SQLiteCloud
        if db_path.startswith('sqlitecloud://'):
            if not SQLITECLOUD_AVAILABLE:
                raise ImportError("sqlitecloud package is required for SQLiteCloud connections")
            import sqlitecloud
            _local.connection = sqlitecloud.connect(db_path)
            _local.connection.row_factory = sqlite3.Row
        else:
            # Local SQLite file
            if db_path.startswith('sqlite:///'):
                db_path = db_path[10:]  # Remove sqlite:/// prefix
                
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            _local.connection = sqlite3.connect(db_path, check_same_thread=False)
            _local.connection.row_factory = sqlite3.Row
        
        _local.connection.execute('PRAGMA foreign_keys = ON')
        
    return _local.connection

@contextmanager
def get_db_transaction(db_url=None):
    """Context manager for database transactions with proper locking"""
    conn = get_db_connection(db_url)
    try:
        # Use BEGIN IMMEDIATE for exclusive transactions
        conn.execute('BEGIN IMMEDIATE')
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def init_db(db_url=None):
    """Initialize database with tables and indexes"""
    conn = get_db_connection(db_url)
    
    # Create tables
    conn.executescript("""
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK (perfil IN ('admin', 'medico', 'coordenacao')),
            especialidade TEXT,
            ativo BOOLEAN DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Patients table
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            data_nascimento DATE NOT NULL,
            telefone TEXT,
            local_referencia TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Evaluations table
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            medico_id INTEGER NOT NULL,
            especialidade TEXT NOT NULL,
            local TEXT NOT NULL,
            observacoes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
            FOREIGN KEY (medico_id) REFERENCES users (id)
        );
        
        -- Evaluation therapies (many-to-many)
        CREATE TABLE IF NOT EXISTS avaliacao_terapias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avaliacao_id INTEGER NOT NULL,
            terapia TEXT NOT NULL,
            FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes (id) ON DELETE CASCADE
        );
        
        -- Procedures table
        CREATE TABLE IF NOT EXISTS procedimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            especialidade TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendente' 
                CHECK (estado IN ('pendente', 'alocado', 'em_atendimento', 'concluido')),
            medico_responsavel_id INTEGER,
            motivo_devolucao TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
            FOREIGN KEY (medico_responsavel_id) REFERENCES users (id)
        );
        
        -- Audit log table
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            acao TEXT NOT NULL,
            detalhe TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        -- Specialties table
        CREATE TABLE IF NOT EXISTS especialidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ativo BOOLEAN DEFAULT 1
        );
        
        -- Locations table
        CREATE TABLE IF NOT EXISTS locais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ativo BOOLEAN DEFAULT 1
        );
    """)
    
    # Create indexes for performance
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON pacientes (cpf);
        CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes (nome);
        CREATE INDEX IF NOT EXISTS idx_avaliacoes_paciente ON avaliacoes (paciente_id);
        CREATE INDEX IF NOT EXISTS idx_avaliacoes_medico ON avaliacoes (medico_id);
        CREATE INDEX IF NOT EXISTS idx_procedimentos_paciente_especialidade 
            ON procedimentos (paciente_id, especialidade);
        CREATE INDEX IF NOT EXISTS idx_procedimentos_estado ON procedimentos (estado);
        CREATE INDEX IF NOT EXISTS idx_procedimentos_medico ON procedimentos (medico_responsavel_id);
        CREATE INDEX IF NOT EXISTS idx_auditoria_user ON auditoria (user_id);
        CREATE INDEX IF NOT EXISTS idx_auditoria_acao ON auditoria (acao);
    """)
    
    conn.commit()
