from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length


class HabitForm(FlaskForm):
    """Форма для привычки"""
    id = HiddenField('id')
    name = StringField('Название', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=1, max=255, message='Название должно быть от 1 до 255 символов')
    ])
    delete = SubmitField('Удалить')
    submit = SubmitField('Сохранить')
