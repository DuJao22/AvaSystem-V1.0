# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from models.database import get_db_connection

def log_action(user_id, acao, detalhe):
    """Log an action to the audit table"""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO auditoria (user_id, acao, detalhe)
        VALUES (?, ?, ?)
    """, (user_id, acao, detalhe))
    conn.commit()

def get_audit_logs(limit=100, offset=0, user_id=None, acao=None):
    """Get audit logs with optional filters"""
    conn = get_db_connection()
    
    where_conditions = []
    params = []
    
    if user_id:
        where_conditions.append("a.user_id = ?")
        params.append(user_id)
    
    if acao:
        where_conditions.append("a.acao = ?")
        params.append(acao)
    
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    params.extend([limit, offset])
    
    rows = conn.execute(f"""
        SELECT a.*, u.nome as user_nome
        FROM auditoria a
        LEFT JOIN users u ON a.user_id = u.id
        {where_clause}
        ORDER BY a.criado_em DESC
        LIMIT ? OFFSET ?
    """, params).fetchall()
    
    return [dict(row) for row in rows]

def count_audit_logs(user_id=None, acao=None):
    """Count audit logs with optional filters"""
    conn = get_db_connection()
    
    where_conditions = []
    params = []
    
    if user_id:
        where_conditions.append("user_id = ?")
        params.append(user_id)
    
    if acao:
        where_conditions.append("acao = ?")
        params.append(acao)
    
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    count = conn.execute(f"""
        SELECT COUNT(*) FROM auditoria {where_clause}
    """, params).fetchone()[0]
    
    return count
