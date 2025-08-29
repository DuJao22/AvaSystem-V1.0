# Sistema de Registro de Avaliações - Clínica TEA

Sistema web completo para gestão de avaliações e distribuição de procedimentos em clínicas especializadas em Transtorno do Espectro Autista (TEA).

**Criado por João Layon**

## 📋 Descrição

O Sistema TEA é uma aplicação web desenvolvida para facilitar o registro, distribuição e gestão de avaliações clínicas e procedimentos terapêuticos em clínicas especializadas em TEA. O sistema oferece controle de acesso baseado em perfis, distribuição inteligente de pacientes por especialidade e relatórios detalhados.

## ✨ Funcionalidades Principais

### 🔐 Autenticação e Controle de Acesso
- Login seguro com hash de senhas
- Três perfis de usuário: Administrador, Médico e Coordenação/Recepção
- Controle de permissões baseado em roles (RBAC)
- Rate limiting para proteção contra ataques de força bruta

### 👥 Gestão de Pacientes
- Cadastro completo com validação de CPF
- Busca avançada por nome, CPF e telefone
- Histórico completo de avaliações e procedimentos
- Cálculo automático de idade

### 🏥 Sistema de Avaliações
- Registro de avaliações por especialidade médica
- Seleção múltipla de terapias recomendadas
- Geração automática de procedimentos pendentes
- Observações detalhadas

### 🔄 Centro de Distribuição
- Visualização em tabela e kanban
- Sistema de "puxar para minha equipe" com exclusividade
- Bloqueio automático por especialidade
- Controle de estados: pendente → alocado → em atendimento → concluído
- Funcionalidade de devolução com motivo

### 📊 Relatórios e Estatísticas
- Relatórios por especialidade e médico
- Exportação em CSV
- Gráficos de progresso e distribuição
- Dashboard com métricas em tempo real

### 🔍 Auditoria Completa
- Log de todas as ações importantes
- Rastreabilidade completa
- Histórico de mudanças de estado

## 🛠 Tecnologias Utilizadas

### Backend
- **Flask** - Framework web Python
- **SQLite3** - Banco de dados (com suporte para SQLiteCloud)
- **Werkzeug** - Segurança e utilitários
- **Flask-WTF** - Proteção CSRF
- **python-dotenv** - Gerenciamento de variáveis de ambiente

### Frontend
- **HTML5** - Estrutura semântica
- **TailwindCSS** - Framework CSS via CDN
- **JavaScript Vanilla** - Interatividade
- **Feather Icons** - Iconografia
- **Jinja2** - Template engine

### Segurança
- Hash seguro de senhas com Werkzeug
- Proteção CSRF
- Validação de entrada e sanitização
- Queries parametrizadas para prevenção de SQL injection
- Rate limiting básico

## 📁 Estrutura do Projeto

