#!/usr/bin/env python3
# Sistema de Registro de Avaliações - Clínica TEA
# Criado por João Layon

"""
Database initialization script
Creates all necessary tables and indexes for the TEA Clinic system
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models.database import init_db
from utils.helpers import ensure_specialties_and_locations

def create_database():
    """Initialize the database with all tables and default data"""
    
    print("Inicializando banco de dados do Sistema TEA...")
    
    # Ensure instance directory exists
    instance_dir = Path("instance")
    instance_dir.mkdir(exist_ok=True)
    
    # Initialize database with tables and indexes
    db_url = Config.DATABASE_URL
    print(f"Usando banco de dados: {db_url}")
    
    try:
        # Create tables and indexes
        init_db(db_url)
        print("✓ Tabelas e índices criados com sucesso")
        
        # Ensure default specialties and locations exist
        ensure_specialties_and_locations()
        print("✓ Especialidades e locais padrão adicionados")
        
        print("\n" + "="*50)
        print("BANCO DE DADOS INICIALIZADO COM SUCESSO!")
        print("="*50)
        print("Para popular o banco com dados de teste, execute:")
        print("python scripts/seed.py")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_database()
