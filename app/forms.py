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
            ("1", "Каждый день"),
            ("2", "Каждые 2 дня"),
            ("3", "Каждые 3 дня"),
            ("7", "Каждую неделю"),
            ("14", "Каждые 2 недели"),
            ("30", "Каждый месяц"),
        ],
        default="7",
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
            ("1", "Каждый день"),
            ("2", "Каждые 2 дня"),
            ("3", "Каждые 3 дня"),
            ("7", "Каждую неделю"),
            ("14", "Каждые 2 недели"),
            ("30", "Каждый месяц"),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Сохранить")


class TaskForm(FlaskForm):
    title = StringField("Название задачи", validators=[DataRequired(), Length(max=128)])
