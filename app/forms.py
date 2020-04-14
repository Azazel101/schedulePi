from flask_wtf          import FlaskForm
from wtforms			import DateField, StringField, TextField, IntegerField, FloatField, BooleanField, SubmitField, HiddenField, SelectField, validators
from wtforms.validators import InputRequired, DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms_components import TimeField


from app.models          import Pin, DailySchedule, WeeklySchedule

def pin_query():
    return Pin.query

class DailyScheduleForm(FlaskForm):
    Time       = TimeField("Time", validators=[DataRequired()])
    Pin      = QuerySelectField("Pin", query_factory=pin_query, allow_blank=False, get_label='name')
    Duration  = IntegerField('Duration', validators=[DataRequired()])
    submit    = SubmitField("Add")

avalible_pins = [(3,'3'),
                (5,'5'),
                (7,'7'),
                (8,'8'),
                (10,'10'),
                (11,'11'),
                (12,'12'),
                (13,'13'),
                (15,'15'),
                (16,'16'),
                (18,'18'),
                (19,'19'),
                (21,'21'),
                (22,'22'),
                (23,'23'),
                (24,'24'),
                (26,'26')]

select_io = [(False,'Input'),(True,'Output')]

class PinForm(FlaskForm):
    Name       = StringField("Time", validators=[DataRequired()])
    Pin        = SelectField("Pin", choices=avalible_pins)
    IO         = SelectField('I/O', choices=select_io, validators=[DataRequired()])
    submit     = SubmitField("Add")