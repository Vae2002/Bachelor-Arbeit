from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired

class MemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    daily_calories = FloatField('Daily Calories')
    protein_grams = FloatField('Protein (g)')
    fat_grams = FloatField('Fat (g)')
    carbs_grams = FloatField('Carbs (g)')

    cuisines = SelectMultipleField('Cuisines', choices=[
        ('Italian', 'Italian'), ('Chinese', 'Chinese')
    ])

    allergies = SelectMultipleField('Allergies', choices=[
        ('Peanuts', 'Peanuts'), ('Dairy', 'Dairy')
    ])

    dietary_restrictions = SelectMultipleField('Dietary Restrictions', choices=[
        ('Low Salt', 'Low Salt'), ('Low Sugar', 'Low Sugar'), 
        ('Low Fat', 'Low Fat'), ('Gluten Free', 'Gluten Free')
    ])

    submit = SubmitField('Add Member')