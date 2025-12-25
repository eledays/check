from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo


class HabitCreatingForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
