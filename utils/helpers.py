# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

from datetime import datetime
from models.database import get_db_connection
from config import Config

def validate_date(date_string):
    """Validate date string in YYYY-MM-DD format"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def format_date(date_string):
    """Format date for display"""
    if not date_string:
        return ''
    
    try:
        if isinstance(date_string, str):
            dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        else:
            dt = date_string
        return dt.strftime('%d/%m/%Y')
    except:
        return date_string

def format_datetime(datetime_string):
    """Format datetime for display"""
    if not datetime_string:
        return ''
    
    try:
        if isinstance(datetime_string, str):
            dt = datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
        else:
            dt = datetime_string
        return dt.strftime('%d/%m/%Y às %H:%M')
    except:
        return datetime_string

def get_specialties():
    """Get list of available specialties"""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT nome FROM especialidades WHERE ativo = 1 ORDER BY nome
    """).fetchall()
    
    specialties = [row['nome'] for row in rows]
    
    # If no specialties in database, return defaults
    if not specialties:
        return Config.DEFAULT_SPECIALTIES
    
    return specialties

def get_locations():
    """Get list of available locations"""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT nome FROM locais WHERE ativo = 1 ORDER BY nome
    """).fetchall()
    
    locations = [row['nome'] for row in rows]
    
    # If no locations in database, return defaults
    if not locations:
        return Config.DEFAULT_LOCATIONS
    
    return locations

def ensure_specialties_and_locations():
    """Ensure default specialties and locations exist in database"""
    conn = get_db_connection()
    
    # Check and add default specialties
    for specialty in Config.DEFAULT_SPECIALTIES:
        existing = conn.execute("""
            SELECT id FROM especialidades WHERE nome = ?
        """, (specialty,)).fetchone()
        
        if not existing:
            conn.execute("""
                INSERT INTO especialidades (nome) VALUES (?)
            """, (specialty,))
    
    # Check and add default locations
    for location in Config.DEFAULT_LOCATIONS:
        existing = conn.execute("""
            SELECT id FROM locais WHERE nome = ?
        """, (location,)).fetchone()
        
        if not existing:
            conn.execute("""
                INSERT INTO locais (nome) VALUES (?)
            """, (location,))
    
    conn.commit()

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    try:
        if isinstance(birth_date, str):
            birth_dt = datetime.strptime(birth_date, '%Y-%m-%d')
        else:
            birth_dt = birth_date
        
        today = datetime.now()
        age = today.year - birth_dt.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < birth_dt.month or (today.month == birth_dt.month and today.day < birth_dt.day):
            age -= 1
        
        return age
    except:
        return None

def paginate(query_result, page, per_page):
    """Simple pagination helper"""
    total = len(query_result)
    start = (page - 1) * per_page
    end = start + per_page
    
    items = query_result[start:end]
    
    has_prev = page > 1
    has_next = end < total
    
    return {
        'items': items,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None,
        'total': total
    }
