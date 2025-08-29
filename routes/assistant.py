from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from utils.auth import require_login
from services.ai_assistant import AIAssistant
from models.audit import log_action

assistant_bp = Blueprint('assistant', __name__)

@assistant_bp.route('/')
@require_login
def chat():
    """Página principal do assistente IA"""
    return render_template('assistant/chat.html')

@assistant_bp.route('/ask', methods=['POST'])
@require_login
def ask_question():
    """API endpoint para fazer perguntas ao assistente"""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'Pergunta não fornecida'
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                'success': False,
                'error': 'Pergunta não pode estar vazia'
            }), 400
        
        # Criar instância do assistente
        assistant = AIAssistant()
        
        # Obter nome do usuário para logs
        user_name = session.get('user_nome', 'Usuário')
        user_id = session.get('user_id')
        
        # Processar pergunta
        result = assistant.ask_question(question, user_name)
        
        # Log da ação
        if user_id:
            log_action(user_id, 'ai_question_asked', f'Pergunta ao assistente IA: {question[:100]}...')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno do servidor: {str(e)}'
        }), 500

@assistant_bp.route('/examples')
@require_login  
def examples():
    """Página com exemplos de perguntas"""
    examples_list = [
        {
            'category': 'Localização de Pacientes',
            'questions': [
                'Onde está o paciente João Silva?',
                'Com qual médico está Maria Santos?',
                'Qual o status do paciente com CPF 123.456.789-00?'
            ]
        },
        {
            'category': 'Avaliações',
            'questions': [
                'Quem avaliou Ana Costa?',
                'Qual médico fez a primeira avaliação de Pedro Oliveira?',
                'Quais médicos já atenderam Carlos Pereira?'
            ]
        },
        {
            'category': 'Médicos e Especialidades',
            'questions': [
                'Quais pacientes estão com Dr. Roberto?',
                'Quantos pacientes tem a Dra. Fernanda?',
                'Quem são os médicos de Fonoaudiologia?'
            ]
        }
    ]
    
    return render_template('assistant/examples.html', examples=examples_list)