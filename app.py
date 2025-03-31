import os
from flask import Flask, render_template, request, redirect, url_for, flash
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
    groceries = db.relationship('GroceryItem', backref='user', lazy=True)

# GroceryItem Model
class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchased = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route (requires login)
@app.route('/')
@login_required
def grocery():
    items = GroceryItem.query.filter_by(user_id=current_user.id).all()
    return render_template('grocery_list.html', items=items, user=current_user)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if username already exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists! Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create new user
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password matches
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('grocery'))
        else:
            flash('Invalid credentials. Please register if you are new.', 'danger')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/diet_calculator', methods=['GET', 'POST'])
def diet_calculator():
    if request.method == 'POST':
        # Get input data from the form
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        age = int(request.form['age'])
        gender = request.form['gender']
        goal = request.form['goal']
        activity = request.form['activity']
        
        # Optional inputs for body measurements
        neck = float(request.form['neck']) if request.form['neck'] else None
        waist = float(request.form['waist']) if request.form['waist'] else None
        hip = float(request.form['hip']) if request.form['hip'] else None
        
        # Calculate BMR using different methods depending on gender and measurements
        if gender == 'male':
            # Mifflin-St Jeor formula for males
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            # For females, we use the US Navy method or a more precise version using waist and neck
            if neck and waist:
                bmr = 66 + (13.75 * weight) + (5 * height) - (6.75 * age) + (6.75 * (waist - neck))
            else:
                # If no waist or neck, use Mifflin-St Jeor for females
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        # Physical Activity Multipliers
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'intense': 1.725
        }
        tdee = bmr * activity_multipliers[activity]
        
        # Macronutrient breakdown
        protein_percentage = float(request.form['protein']) / 100
        fat_percentage = float(request.form['fat']) / 100
        carb_percentage = 1 - protein_percentage - fat_percentage
        
        # Calculate grams of each macronutrient
        protein_grams = (tdee * protein_percentage) / 4
        fat_grams = (tdee * fat_percentage) / 9
        carbs_grams = (tdee * carb_percentage) / 4

        # Return the calculated data to the template
        return render_template('diet_calculator.html', 
                               bmr=bmr, 
                               tdee=tdee, 
                               protein_grams=protein_grams, 
                               fat_grams=fat_grams, 
                               carbs_grams=carbs_grams)
    
    # If GET request, render the form page
    return render_template('diet_calculator.html')

# GroceryItem routes
@app.route('/add', methods=['POST'])
@login_required
def add_item():
    name = request.form.get('name')
    quantity = request.form.get('quantity', type=int)

    if name and quantity:
        new_item = GroceryItem(name=name, quantity=quantity, user_id=current_user.id)
        db.session.add(new_item)
        db.session.commit()

    return redirect(url_for('grocery'))

@app.route('/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    
    if item.user_id != current_user.id:  # Prevent unauthorized deletion
        flash("You can't delete someone else's item!", "danger")
        return redirect(url_for('grocery'))

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('grocery'))

@app.route('/clear_all', methods=['POST'])
@login_required
def clear_all():
    GroceryItem.query.filter_by(purchased=True, user_id=current_user.id).delete()
    db.session.commit()
    
    return {"success": True, "message": "All purchased items cleared!"} 

@app.route('/toggle_purchased/<int:item_id>', methods=['POST'])
@login_required
def toggle_purchased(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    
    if item.user_id != current_user.id:
        return {"error": "Unauthorized action!"}, 403

    item.purchased = not item.purchased
    db.session.commit()

    return {"success": True, "purchased": item.purchased} 

# Profile Page
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# Update Profile Route
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user = current_user

    user.username = request.form['username']
    user.email = request.form['email']
    user.bio = request.form['bio']

    # Handle profile picture upload
    if 'profile_pic' in request.files:
        profile_pic = request.files['profile_pic']
        if profile_pic.filename:
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_pic = filename

    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

# Recreate the database (Run this ONCE after deleting `grocery.db`)
def reset_database():
    if os.path.exists("grocery.db"):
        os.remove("grocery.db")  # Delete old database file
    db.create_all()
    print("Database reset and recreated successfully!")

# Initialize Database
if __name__ == '__main__':
    with app.app_context():
        reset_database()  # Call this function ONCE to reset
    app.run(debug=True)
