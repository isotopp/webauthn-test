"""Shared Flask extension singletons.

This module hosts extension instances that must be imported across multiple
modules without creating circular initialization dependencies.

Constraint:
- objects are declared once and initialized in the app factory only
"""

from flask_security import Security
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
security = Security()
