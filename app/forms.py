from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional


class ProjectForm(FlaskForm):
    name = StringField("Название проекта", validators=[DataRequired(), Length(max=128)])
    short_name = StringField("Короткое имя", validators=[DataRequired(), Length(max=16)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=256)])
    goals = TextAreaField("Цели", validators=[Optional(), Length(max=4096)])
    periodicity = SelectField(
        "Периодичность возврата",
        choices=[
            ('DAILY', 'Каждый день'),
            ('WEEKLY', 'Каждую неделю'),
            ('BIWEEKLY', 'Каждые 2 недели'),
            ('MONTHLY', 'Каждый месяц'),
            ('QUARTERLY', 'Каждые 3 месяца'),
        ],
        default='WEEKLY',
        validators=[DataRequired()]
    )
    submit = SubmitField("Создать")


class EditProjectForm(FlaskForm):
    name = StringField("Название проекта", validators=[DataRequired(), Length(max=128)])
    short_name = StringField("Короткое имя", validators=[DataRequired(), Length(max=16)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=256)])
    goals = TextAreaField("Цели", validators=[Optional(), Length(max=4096)])
    periodicity = SelectField(
        "Периодичность возврата",
        choices=[
            ('DAILY', 'Каждый день'),
            ('WEEKLY', 'Каждую неделю'),
            ('BIWEEKLY', 'Каждые 2 недели'),
            ('MONTHLY', 'Каждый месяц'),
            ('QUARTERLY', 'Каждые 3 месяца'),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Сохранить")


class TaskForm(FlaskForm):
    title = StringField("Название задачи", validators=[DataRequired(), Length(max=128)])
