# ==========================================================================
# Interview Studio - Sprint 2, Task S2-1.4: questions, rubrics, roles
# Story: US-2 Receive Interview Questions
# Author: Riket Sanketkumar Patel (GitHub: Riketpatel25)
# This file: the skill list and the 4 job roles with their skill weights.
# ==========================================================================
"""
S2-1.4 roles and skills (source of truth for the skills, roles, and role_skills tables).

SKILLS   every skill a question or role may use (lowercase, unique). The behavioral
         skills are here from day 1 so behavioral_data.py (S2-3.1) can tag against them.
ROLES    {name, keywords, technical_share, skills: {skill: weight}}
         keywords        whole-word matches for the job-title fallback matcher (S2-1.3)
         technical_share share of technical questions in a Mixed interview (0 to 1)
         skills          weights add up to 1; the interview builder samples by weight
"""

TECHNICAL_SKILLS = [
    "data structures", "algorithms", "oop", "databases", "sql", "web apis",
    "operating systems", "networking", "software engineering", "python", "system design",
    "statistics", "data visualization", "data cleaning",
    "troubleshooting", "hardware", "security",
]

BEHAVIORAL_SKILLS = [
    "communication", "teamwork", "conflict resolution", "customer service", "problem solving",
]

SKILLS = TECHNICAL_SKILLS + BEHAVIORAL_SKILLS

ROLES = [
    {
        "name": "Software Engineer",
        "keywords": ["software", "engineer", "developer", "programmer", "backend", "frontend", "full stack"],
        "technical_share": 0.7,
        "skills": {
            "data structures": 0.15, "algorithms": 0.15, "oop": 0.1, "databases": 0.1,
            "web apis": 0.1, "system design": 0.1, "software engineering": 0.1,
            "problem solving": 0.1, "teamwork": 0.1,
        },
    },
    {
        "name": "Data Analyst",
        "keywords": ["data", "analyst", "analytics", "bi", "business intelligence", "reporting"],
        "technical_share": 0.6,
        "skills": {
            "sql": 0.3, "statistics": 0.2, "data visualization": 0.15, "data cleaning": 0.1,
            "communication": 0.15, "problem solving": 0.1,
        },
    },
    {
        "name": "IT Support",
        "keywords": ["it", "help desk", "helpdesk", "technician", "service desk", "desktop support", "support"],
        "technical_share": 0.6,
        "skills": {
            "troubleshooting": 0.3, "networking": 0.2, "operating systems": 0.1, "security": 0.1,
            "hardware": 0.05, "customer service": 0.15, "communication": 0.1,
        },
    },
    {
        "name": "Customer Service",
        "keywords": ["customer", "call center", "agent", "service", "representative", "client"],
        "technical_share": 0.0,  # behavioral only
        "skills": {
            "customer service": 0.4, "communication": 0.3, "conflict resolution": 0.2, "problem solving": 0.1,
        },
    },
]
