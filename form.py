from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import InputRequired, ValidationError, NumberRange


def len_check(form, field):
    if len(field.data) > 50:
        raise ValidationError('Input length must be less than 50 characters')


class PantryForm(FlaskForm):
    name = StringField('name', validators=[InputRequired(), len_check])
    count = IntegerField('count', validators=[InputRequired(), NumberRange(min=1)])
