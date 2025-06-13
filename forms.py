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
        ('asian', 'Asian'),
        ('italian', 'Italian'),
        ('mexican', 'Mexican'),
        ('indian', 'Indian'),
        ('mediterranean', 'Mediterranean')
    ])

    allergies = SelectMultipleField('Allergies', choices=[
        ('milk', 'Milk'),
        ('eggs', 'Eggs'),
        ('peanuts', 'Peanuts'),
        ('tree_nuts', 'Tree Nuts'),
        ('soy', 'Soy'),
        ('wheat', 'Wheat'),
        ('fish', 'Fish'),
        ('shellfish', 'Shellfish'),
        ('sesame', 'Sesame')
    ])

    dietary_restrictions = SelectMultipleField('Dietary Restrictions', choices=[
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('gluten_free', 'Gluten-Free'),
        ('low_carb', 'Low Carb'),
        ('low_sugar', 'Low Sugar'),
        ('low_fat', 'Low Fat'),
        ('low_sodium', 'Low Sodium'),
        ('high_protein', 'High Protein'),
        ('low_cholesterol', 'Low Cholestrol'),
        ('halal', 'Halal')
    ])

    submit = SubmitField('Add Member')