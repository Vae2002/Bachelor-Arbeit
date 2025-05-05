from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

# =================== DATABASE ===================

# Initialize Database
db = SQLAlchemy()

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(300), nullable=True, default="default.jpg")

    # Add new fields for daily calorie intake and macronutrients
    daily_calories = db.Column(db.Float, nullable=True)
    protein_grams = db.Column(db.Float, nullable=True)
    fat_grams = db.Column(db.Float, nullable=True)
    carbs_grams = db.Column(db.Float, nullable=True)

    cuisines = db.Column(db.Text, nullable=True, default="[]")  
    allergies = db.Column(db.Text, nullable=True, default="[]") 
    dietary_restrictions = db.Column(db.Text, nullable=True, default="[]")

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)


class MealPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)    
    recipe_name = db.Column(db.String(255), nullable=False) 
    recipe_calories = db.Column(db.String(255), nullable=False)
    recipe_macro = db.Column(db.String(255), nullable=False)
    recipe_micro = db.Column(db.String(255), nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional: backref to User
    user = db.relationship('User', backref='meal_plans')