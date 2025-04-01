import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =================== AUTHENTICATION ===================
# Initialize Database
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(300), nullable=True, default="default.jpg")
    
    # Add new fields with default values
    cuisines = db.Column(db.Text, nullable=True, default="[]")  # Store as JSON string
    allergies = db.Column(db.Text, nullable=True, default="[]") 
    dietary_restrictions = db.Column(db.Text, nullable=True, default="[]")


# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already taken!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# =================== PROFILE PAGE ===================
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Ensure old users don't break due to missing fields
    if current_user.cuisines is None:
        current_user.cuisines = "[]"
    if current_user.allergies is None:
        current_user.allergies = "[]"
    if current_user.dietary_restrictions is None:
        current_user.dietary_restrictions = "[]"
    
    # Handle form submission
    if request.method == "POST":
        # Update user fields
        current_user.username = request.form.get("username")
        current_user.email = request.form.get("email")
        current_user.bio = request.form.get("bio")

        # Handle profile picture upload
        if "profile_pic" in request.files:
            profile_pic = request.files["profile_pic"]
            if profile_pic.filename != "":
                pic_filename = f"{current_user.id}_{secure_filename(profile_pic.filename)}"
                profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_filename))
                current_user.profile_pic = pic_filename  # Save filename to user model

        # Save selected preferences (convert lists to JSON strings)
        current_user.cuisines = str(request.form.getlist("cuisines[]"))
        current_user.allergies = str(request.form.getlist("allergies[]"))
        current_user.dietary_restrictions = str(request.form.getlist("dietary_restrictions[]"))

        # Commit changes to the database
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))  # Redirect to refresh the page

    return render_template("profile.html", user=current_user)

# =================== HOMEPAGE ===================
@app.route('/')
@login_required
def home():
    return render_template('index.html', user=current_user)

# =================== DIET CALCULATOR ===================
@app.route('/diet_calculator', methods=['GET', 'POST'])
@login_required
def diet_calculator():
    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        age = int(request.form['age'])
        gender = request.form['gender']
        activity = request.form['activity']

        # Optional body measurements
        neck = float(request.form['neck']) if request.form.get('neck') else None
        waist = float(request.form['waist']) if request.form.get('waist') else None
        hip = float(request.form['hip']) if request.form.get('hip') else None

        # BMR Calculation
        if gender == 'male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            if neck and waist:
                bmr = 655 + (9.6 * weight) + (1.8 * height) - (4.7 * age) + (6.75 * (waist - neck))
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # Activity Multipliers
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'intense': 1.725
        }
        tdee = bmr * activity_multipliers[activity]

        # Macronutrient Breakdown
        protein_percentage = float(request.form['protein']) / 100
        fat_percentage = float(request.form['fat']) / 100
        carb_percentage = 1 - protein_percentage - fat_percentage

        protein_grams = (tdee * protein_percentage) / 4
        fat_grams = (tdee * fat_percentage) / 9
        carbs_grams = (tdee * carb_percentage) / 4

        return render_template('diet_calculator.html', bmr=bmr, tdee=tdee, protein_grams=protein_grams, fat_grams=fat_grams, carbs_grams=carbs_grams)
    
    return render_template('diet_calculator.html')

# =================== GROCERY LIST ===================
# GroceryItem Model
class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchased = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Grocery List Routes
@app.route('/grocery')
@login_required
def grocery():
    groceries = GroceryItem.query.filter_by(user_id=current_user.id).all()
    return render_template('grocery_list.html', groceries=groceries)

@app.route('/add', methods=['POST'])
@login_required
def add_item():
    name = request.form.get('name')
    quantity = request.form.get('quantity', type=int)

    if not quantity:
        quantity = 1

    if name:
        new_item = GroceryItem(name=name, quantity=quantity, user_id=current_user.id)
        db.session.add(new_item)
        db.session.commit()

    return redirect(url_for('grocery'))

@app.route('/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('grocery'))

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('grocery'))

@app.route('/clear_all', methods=['POST'])
@login_required
def clear_all():
    GroceryItem.query.filter_by(purchased=True, user_id=current_user.id).delete()
    db.session.commit()
    return jsonify(success=True, message="All purchased items cleared!")

@app.route('/toggle_purchased/<int:item_id>', methods=['POST'])
@login_required
def toggle_purchased(item_id):
    item = GroceryItem.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        return jsonify(error="Unauthorized action!"), 403

    item.purchased = not item.purchased
    db.session.commit()

    return jsonify(success=True, purchased=item.purchased)

@app.route('/rename/<int:item_id>', methods=['POST'])
@login_required
def rename_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        return jsonify(error="Unauthorized action!"), 403

    new_name = request.form.get('new_name')
    new_quantity = request.form.get('new_quantity', type=int)

    if new_name:
        item.name = new_name
    if new_quantity:
        item.quantity = new_quantity

    db.session.commit()
    return jsonify(success=True)


# =================== DATABASE ===================

# # Recreate the database (Run this ONCE after deleting `grocery.db`)
# def reset_database():
#     if os.path.exists("grocery.db"):
#         os.remove("grocery.db")  # Delete old database file
#     db.create_all()
#     print("Database reset and recreated successfully!")

# # Initialize Database
# if __name__ == '__main__':
#     with app.app_context():
#         reset_database()  # Call this function ONCE to reset
#     app.run(debug=True)

# Initialize Database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
