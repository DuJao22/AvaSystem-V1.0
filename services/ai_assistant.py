import json
import os
from google import genai
from google.genai import types
from models.patient import Patient
from models.user import User
from models.evaluation import Evaluation
from models.procedure import Procedure
from models.database import get_db_connection

class AIAssistant:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
        
        # IMPORTANT: Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
        # do not change this unless explicitly requested by the user
        self.client = genai.Client(api_key=api_key)
        
    def get_patient_info(self, patient_query):
        """Busca informações do paciente por nome ou CPF"""
        try:
            # Tenta buscar por CPF primeiro (números apenas)
            clean_query = ''.join(filter(str.isdigit, patient_query))
            if len(clean_query) == 11:  # CPF
                patient = Patient.get_by_cpf(clean_query)
                if patient:
                    return [patient]
            
            # Se não encontrou por CPF, busca por nome
            patients = Patient.search(patient_query, limit=5)
            return patients
        except Exception as e:
            print(f"Erro ao buscar paciente: {e}")
            return []
    
    def get_patient_current_status(self, patient_id):
        """Obtém o status atual do paciente - com que profissional está"""
        try:
            conn = get_db_connection()
            
            # Busca procedimentos ativos (alocado ou em atendimento)
            active_procedures = conn.execute("""
                SELECT p.*, u.nome as medico_nome, u.especialidade
                FROM procedimentos p
                LEFT JOIN users u ON p.medico_responsavel_id = u.id
                WHERE p.paciente_id = ? AND p.estado IN ('alocado', 'em_atendimento')
                ORDER BY p.atualizado_em DESC
            """, (patient_id,)).fetchall()
            
            return [dict(row) for row in active_procedures]
        except Exception as e:
            print(f"Erro ao buscar status do paciente: {e}")
            return []
    
    def get_patient_evaluations(self, patient_id):
        """Obtém avaliações do paciente"""
        try:
            evaluations = Evaluation.get_by_patient_id(patient_id)
            return evaluations
        except Exception as e:
            print(f"Erro ao buscar avaliações: {e}")
            return []
    
    def get_doctor_info(self, doctor_query):
        """Busca informações do médico por nome"""
        try:
            conn = get_db_connection()
            doctors = conn.execute("""
                SELECT * FROM users 
                WHERE perfil = 'medico' AND ativo = 1 
                AND nome LIKE ?
                ORDER BY nome
                LIMIT 5
            """, (f"%{doctor_query}%",)).fetchall()
            
            return [dict(row) for row in doctors]
        except Exception as e:
            print(f"Erro ao buscar médico: {e}")
            return []
    
    def prepare_context_data(self, user_question):
        """Prepara dados do contexto baseado na pergunta do usuário"""
        context_data = {
            "patients": [],
            "current_assignments": [],
            "evaluations": [],
            "doctors": []
        }
        
        # Detecta se a pergunta menciona pacientes específicos
        question_lower = user_question.lower()
        
        # Procura por nomes próprios ou CPFs na pergunta
        words = user_question.split()
        for i, word in enumerate(words):
            # Se encontrou um nome próprio (começando com maiúscula)
            if word[0].isupper() and len(word) > 2:
                # Tenta buscar paciente com este nome
                possible_name = word
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    possible_name += " " + words[i + 1]
                
                patients = self.get_patient_info(possible_name)
                if patients:
                    context_data["patients"].extend(patients)
                    
                    # Para cada paciente encontrado, busca status atual e avaliações
                    for patient in patients:
                        status = self.get_patient_current_status(patient.id)
                        context_data["current_assignments"].extend(status)
                        
                        evaluations = self.get_patient_evaluations(patient.id)
                        context_data["evaluations"].extend(evaluations)
        
        # Procura por CPFs na pergunta (sequência de números)
        import re
        cpf_pattern = r'\b\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{2}\b'
        cpfs = re.findall(cpf_pattern, user_question)
        for cpf in cpfs:
            patients = self.get_patient_info(cpf)
            if patients:
                context_data["patients"].extend(patients)
                
                for patient in patients:
                    status = self.get_patient_current_status(patient.id)
                    context_data["current_assignments"].extend(status)
                    
                    evaluations = self.get_patient_evaluations(patient.id)
                    context_data["evaluations"].extend(evaluations)
        
        # Se a pergunta menciona médicos
        if "médico" in question_lower or "doutor" in question_lower or "dra" in question_lower:
            # Tenta extrair nomes de médicos
            for word in words:
                if word[0].isupper() and len(word) > 2:
                    doctors = self.get_doctor_info(word)
                    context_data["doctors"].extend(doctors)
        
        return context_data
    
    def format_context_for_ai(self, context_data):
        """Formata os dados do contexto para enviar à IA"""
        formatted_context = []
        
        if context_data["patients"]:
            formatted_context.append("PACIENTES ENCONTRADOS:")
            for patient in context_data["patients"]:
                formatted_context.append(f"- {patient.nome} (CPF: {patient.cpf})")
        
        if context_data["current_assignments"]:
            formatted_context.append("\nATRIBUIÇÕES ATUAIS:")
            for assignment in context_data["current_assignments"]:
                medico_info = f"Dr(a). {assignment['medico_nome']}" if assignment['medico_nome'] else "Não alocado"
                formatted_context.append(f"- Especialidade: {assignment['especialidade']}, Status: {assignment['estado']}, Médico: {medico_info}")
        
        if context_data["evaluations"]:
            formatted_context.append("\nAVALIAÇÕES:")
            for evaluation in context_data["evaluations"]:
                formatted_context.append(f"- Avaliado por: Dr(a). {evaluation.medico_nome}, Especialidade: {evaluation.especialidade}, Data: {evaluation.criado_em}")
        
        if context_data["doctors"]:
            formatted_context.append("\nMÉDICOS:")
            for doctor in context_data["doctors"]:
                formatted_context.append(f"- Dr(a). {doctor['nome']}, Especialidade: {doctor['especialidade']}")
        
        return "\n".join(formatted_context)
    
    def ask_question(self, user_question, user_name=None):
        """Processa uma pergunta do usuário e retorna uma resposta"""
        try:
            # Prepara dados do contexto
            context_data = self.prepare_context_data(user_question)
            formatted_context = self.format_context_for_ai(context_data)
            
            # Prepara o prompt para a IA
            system_prompt = """Você é um assistente de uma clínica TEA (Transtorno do Espectro Autista). 
            Sua função é responder perguntas sobre pacientes, médicos e procedimentos.
            
            Use as informações fornecidas no contexto para responder às perguntas de forma clara e útil.
            Se não houver informações suficientes, diga isso claramente.
            
            Tipos de perguntas que você pode responder:
            - Onde está o paciente X? (responda com qual médico/especialidade está alocado)
            - Quem avaliou o paciente Y? (responda com o médico que fez a avaliação)
            - Qual o status do paciente Z? (responda com o estado atual do procedimento)
            
            Responda sempre em português e de forma profissional mas amigável."""
            
            user_prompt = f"""Pergunta: {user_question}
            
            Contexto da clínica:
            {formatted_context}
            
            Por favor, responda à pergunta baseando-se nas informações do contexto."""
            
            # Combinar system prompt com user prompt para o Gemini
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Usar o Gemini para gerar a resposta
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=combined_prompt
            )
            
            return {
                "success": True,
                "answer": response.text or "Não consegui processar sua pergunta.",
                "context_found": len(context_data["patients"]) > 0 or len(context_data["doctors"]) > 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar pergunta: {str(e)}",
                "answer": "Desculpe, não consegui processar sua pergunta no momento. Tente novamente."
            }