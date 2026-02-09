from flask_security.forms import RegisterFormV2
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class ExtendedRegisterForm(RegisterFormV2):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=64)],
    )
