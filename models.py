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
    members = db.relationship('Member', backref='user', lazy=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    # Add new fields for daily calorie intake and macronutrients
    daily_calories = db.Column(db.Float, nullable=True)
    protein_grams = db.Column(db.Float, nullable=True)
    fat_grams = db.Column(db.Float, nullable=True)
    carbs_grams = db.Column(db.Float, nullable=True)

    cuisines = db.Column(db.Text, nullable=True, default="[]")  
    allergies = db.Column(db.Text, nullable=True, default="[]") 
    dietary_restrictions = db.Column(db.Text, nullable=True, default="[]")

# GroceryItem Model
class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchased = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


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

# Pantry Model
class Pantry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expired = db.Column(db.Date, nullable=False)
    selected = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)