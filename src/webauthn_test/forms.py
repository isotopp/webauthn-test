"""Flask-Security form extensions for application-specific identity fields.

The app requires a username in addition to email/password. This module adapts
the upstream registration form while preserving Flask-Security validation and
view wiring behavior.
"""

from flask_security.forms import RegisterFormV2
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class ExtendedRegisterForm(RegisterFormV2):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=64)],
    )
