# TEA Clinic Evaluation Management System

## Overview

This is a comprehensive web-based clinical management system designed specifically for TEA (Autism Spectrum Disorder) clinics. The system manages patient evaluations, therapy procedure distribution, and provides detailed reporting capabilities. It features a role-based access control system with three user profiles: Administrator, Doctor, and Coordination/Reception. The system facilitates the complete workflow from patient registration through evaluation to therapy procedure assignment and completion tracking.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Python web framework chosen for its simplicity and flexibility
- **Blueprints**: Modular route organization across auth, dashboard, patients, evaluations, distribution, reports, and admin modules
- **SQLiteCloud**: Cloud-based SQLite database with local fallback support (no ORM)
- **Jinja2**: Template engine for server-side rendering

### Authentication & Authorization
- **Role-Based Access Control (RBAC)**: Three distinct user roles with specific permissions
- **Session Management**: Flask sessions for user state management
- **Password Security**: Werkzeug password hashing for secure credential storage
- **Rate Limiting**: Built-in protection against brute force attacks

### Data Models
- **User Model**: Handles authentication, roles (admin/medico/coordenacao), and specialties
- **Patient Model**: Patient information with CPF validation and search capabilities
- **Evaluation Model**: Clinical evaluations linking patients, doctors, and therapy recommendations
- **Procedure Model**: Therapy procedures with state management (pendente/alocado/em_atendimento/concluido)
- **Audit Model**: Complete activity logging for compliance and traceability

### Distribution Center Architecture
- **Pull-Based Assignment**: Doctors can claim procedures within their specialty
- **Exclusive Allocation**: Prevents double-assignment through database constraints
- **State Machine**: Four-state procedure lifecycle with controlled transitions
- **Kanban/Table Views**: Dual interface options for different user preferences

### Frontend Design
- **Server-Side Rendered**: Traditional web application with Jinja2 templates
- **TailwindCSS**: Utility-first CSS framework for responsive design
- **Feather Icons**: Lightweight icon system for consistent UI
- **Progressive Enhancement**: JavaScript enhances but doesn't replace core functionality

### Database Schema
- **SQLiteCloud**: Cloud-hosted SQLite database with automatic failover to local SQLite
- **Audit Trail**: Complete action logging with user attribution
- **Indexing Strategy**: Optimized queries for patient search and procedure filtering
- **Data Validation**: Both client-side and server-side validation layers
- **Admin Reset**: Capability to reset patient data while preserving doctor records

### Security Features
- **Input Validation**: Comprehensive form validation including CPF validation
- **SQL Injection Protection**: Parameterized queries throughout
- **XSS Prevention**: Jinja2 auto-escaping and secure template practices
- **Session Security**: Secure session configuration with secret key management

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web framework and routing
- **Werkzeug**: Password hashing and security utilities
- **Jinja2**: Template rendering engine
- **SQLiteCloud**: Cloud database service with local SQLite fallback

### Frontend Assets
- **TailwindCSS**: Delivered via CDN for styling
- **Feather Icons**: Icon library delivered via CDN
- **Modern Browsers**: Requires JavaScript support for enhanced features

### Development & Deployment
- **Python 3.7+**: Runtime environment requirement
- **Flask Development Server**: Built-in development server
- **File System**: SQLite database stored in instance directory
- **Environment Variables**: Configuration through .env file support

### Potential Integrations
- **Email Services**: For notifications and user management
- **Backup Solutions**: For data protection and compliance
- **External Authentication**: LDAP/OAuth integration possibility
- **Database Replication**: SQLite database backup and replication strategies