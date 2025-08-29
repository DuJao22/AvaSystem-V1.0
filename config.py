# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Database configuration - SQLiteCloud support
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlitecloud://cmq6frwshz.g4.sqlite.cloud:8860/app.db?apikey=Dor8OwUECYmrbcS5vWfsdGpjCpdm9ecSDJtywgvRw8k')
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    WTF_CSRF_ENABLED = True
    
    # Application settings
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Default specialties
    DEFAULT_SPECIALTIES = [
        'Fonoaudiologia',
        'Psicologia', 
        'Terapia Ocupacional',
        'Fisioterapia',
        'Musicoterapia',
        'Pedagogia/ABA'
    ]
    
    # Default locations
    DEFAULT_LOCATIONS = [
        'Clínica Principal',
        'Unidade Norte',
        'Unidade Sul',
        'Atendimento Domiciliar'
    ]
