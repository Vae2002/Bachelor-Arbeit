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
    profile_pic = db.Column(db.String(300), nullable=True, default="default.jpg")  # Default profile pic

# GroceryItem Model
class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchased = db.Column(db.Boolean, default=False)

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route (requires login)
@app.route('/')
@login_required
def grocery():
    items = GroceryItem.query.all()
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

# GroceryItem routes
@app.route('/add', methods=['POST'])
@login_required
def add_item():
    name = request.form.get('name')
    quantity = request.form.get('quantity', type=int)
    if name and quantity:
        new_item = GroceryItem(name=name, quantity=quantity)
        db.session.add(new_item)
        db.session.commit()
    return redirect(url_for('grocery'))

@app.route('/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('grocery'))

@app.route('/clear_completed')
@login_required
def clear_completed():
    GroceryItem.query.filter_by(purchased=True).delete()
    db.session.commit()
    return redirect(url_for('grocery'))

@app.route('/toggle_purchased/<int:item_id>')
@login_required
def toggle_purchased(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    item.purchased = not item.purchased
    db.session.commit()
    return redirect(url_for('grocery'))

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

# Initialize Database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
