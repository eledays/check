from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ProjectForm(FlaskForm):
    name = StringField("Название проекта", validators=[DataRequired(), Length(max=128)])
    short_name = StringField("Короткое имя", validators=[DataRequired(), Length(max=16)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=256)])
    goals = TextAreaField("Цели", validators=[Optional(), Length(max=4096)])
    submit = SubmitField("Создать")


class EditProjectForm(FlaskForm):
    name = StringField("Название проекта", validators=[DataRequired(), Length(max=128)])
    short_name = StringField("Короткое имя", validators=[DataRequired(), Length(max=16)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=256)])
    goals = TextAreaField("Цели", validators=[Optional(), Length(max=4096)])
    submit = SubmitField("Сохранить изменения")


class TaskForm(FlaskForm):
    title = StringField("Название задачи", validators=[DataRequired(), Length(max=128)])
