"""Flask-Security form extensions for application-specific identity fields.

The app requires a username in addition to email/password. This module adapts
the upstream registration form and customizes login identity handling while
preserving Flask-Security view wiring behavior.
"""

from flask_security.confirmable import requires_confirmation
from flask_security.forms import Form, LoginForm, RegisterFormV2
from flask_security.utils import get_message, hash_password
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class ExtendedRegisterForm(RegisterFormV2):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=64)],
    )


class ExtendedLoginForm(LoginForm):
    email = StringField(
        "Username or Email",
        validators=[DataRequired()],
        render_kw={"autocomplete": "username"},
    )

    def validate(self, **kwargs: object) -> bool:
        if not Form.validate(self, **kwargs):
            return False

        from webauthn_test.models import User

        identity = (self.email.data or "").strip()
        self.ifield = self.email
        self.user = User.query.filter(
            (User.email == identity) | (User.username == identity)
        ).first()

        assert isinstance(self.password.errors, list)
        if self.user is None:
            self.email.errors.append(get_message("USER_DOES_NOT_EXIST")[0])
            hash_password(self.password.data or "")
            return False
        if not self.user.password:
            self.password.errors.append(get_message("INVALID_PASSWORD")[0])
            hash_password(self.password.data or "")
            return False
        if not self.user.verify_and_update_password(self.password.data or ""):
            self.password.errors.append(get_message("INVALID_PASSWORD")[0])
            return False

        self.user_authenticated = True
        self.requires_confirmation = requires_confirmation(self.user)
        if self.requires_confirmation:
            self.email.errors.append(get_message("CONFIRMATION_REQUIRED")[0])
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message("DISABLED_ACCOUNT")[0])
            return False
        return True
