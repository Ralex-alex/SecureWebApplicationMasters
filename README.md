# Secure Web Development Basic CRUD Application

## Project Overview

**Secure Web Development Basic CRUD Application** is a Python Flask-based web application developed to demonstrate secure web application design and implementation. The application provides basic CRUD (Create, Read, Update, Delete) functionality for managing notes while having strong security controls such as authentication, authorization, and input validation.

The project was intentionally designed to initially contain common web vulnerabilities (e.g., SQL Injection, Broken Access Control) which were later identified, exploited, and mitigated. The primary focus of the application is to demonstrate secure coding practices aligned with OWASP Top 10 principles.

---

## Features and Security Objectives

### Core Features
- User registration and login
- Role-based access control (User / Admin)
- CRUD functionality for notes
- Admin panel for managing notes and user accounts
- Secure session handling
- User feedback messages and clean navigation

### Security Objectives
- SQL Injection prevention using parameterized queries
- Secure password storage using hashing
- Role-based authorization enforcement
- Broken Object Level Authorization (BOLA) mitigation
- Stored Cross-Site Scripting (XSS) mitigation
- Password complexity validation
- Database integrity enforcement with constraints

---

## Project Structure

```
ProjectSecureWebApplication/

app.py              # Main Flask application
init_db.py          # Database initialization script
database.db         # SQLite database
requirements.txt    # Python dependencies
README.md           # Project documentation
.gitignore          # Git ignored files
.venv/              # Python virtual environment
```

### Key Files
- **app.py**: Contains all routes, application logic, and security controls.
- **init_db.py**: Initializes the SQLite database and defines schemas.
- **database.db**: Stores users and notes.
- **requirements.txt**: Lists all required Python packages.

---

## Setup and Installation Instructions

### Prerequisites
- Python 3.10 or later
- Git

### Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd ProjectSecureWebApplication
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Run the application:
```bash
python app.py
```

6. Access the application:
```
http://127.0.0.1:5000/
```

---

## Usage Guidelines

### User Workflow
- Register a new account
- Log in using credentials
- View dashboard with username and role
- Create, view, edit, and delete personal notes
- Log out securely

### Admin Workflow
- Log in as admin
- Access Admin Panel
- View and delete any user notes
- Delete non-admin user accounts

---

## Security Improvements

- Password hashing using secure hashing functions
- Parameterized SQL queries to prevent injection attacks
- Role-based access control (RBAC)
- Ownership checks to prevent unauthorized actions
- Output encoding to mitigate stored XSS
- Password complexity enforcement
- Database-level uniqueness constraints

---

## Testing Process

### Security Testing Performed
- SQL Injection testing on authentication and CRUD routes
- Authorization bypass testing
- Stored XSS testing using malicious payloads
- Session and role validation testing

### Tools Used
- Manual browser testing
- SQLite command-line interface
- Flask debug mode

### Key Findings
- SQL Injection vulnerability identified and fixed
- Unauthorized note deletion fixed via access control
- Stored XSS mitigated via output encoding

---

## Contributions and References

### Frameworks and Libraries
- Flask
- SQLite
- Werkzeug

### References
- OWASP Top 10
- Flask Documentation
- Python SQLite Documentation

---

## Final Notes

My project demonstrates a secure development lifecycle including vulnerability discovery, exploitation, remediation, and validation. It highlights practical security controls applied to a real-world type of web application.
