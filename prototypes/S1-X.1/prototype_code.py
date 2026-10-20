# ==========================================================================
# Interview Studio — S1-X.1: GitHub Actions CI
# Owner (Sprint 1): Thunder Oyebi   |   Story: Cross-cutting engineering
#
# This file collects the parts of the shared Interview Studio prototype that
# Thunder Oyebi owns. The prototype was built by the team before tasks were
# assigned; from Sprint 1 on, Thunder maintains and extends this part.
# It is a reference copy — the running app still uses the original files.
#
# HOW IT WORKS
#  - CI runs automatically on every push and pull request, so broken code is caught before it reaches main.
#
# YOUR SPRINT 1 WORK (see the starter file in this folder)
#  - Workflow 1: set up Python, install requirements, run pytest (Arvin's and Hamidat's tests).
#  - Workflow 2: set up Node, run Next.js lint, build and tests.
#  - Make the checks required on pull requests and write a short troubleshooting note.
# ==========================================================================

# --------------------------------------------------------------------------
# FROM: requirements.txt, lines 1-7
# WHAT IT DOES: What CI must install for the Python side.
# --------------------------------------------------------------------------
"""
# Interview Studio — Python dependencies
Flask==3.0.3
python-dotenv==1.0.1
mysql-connector-python==9.0.0
openai==1.51.0
Werkzeug==3.0.4
gunicorn==22.0.0
"""

