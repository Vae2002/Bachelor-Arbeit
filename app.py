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
db = SQLAlchemy()

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'login'

# Bind db to the Flask app
db.init_app(app)

# Initialize LoginManager
login_manager.init_app(app)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(300), nullable=True, default="default.jpg")

    members = db.relationship('Member', backref='user', lazy=True)
    
# Member Model
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    
    # Diet Info
    daily_calories = db.Column(db.Float, nullable=True)
    protein_grams = db.Column(db.Float, nullable=True)
    fat_grams = db.Column(db.Float, nullable=True)
    carbs_grams = db.Column(db.Float, nullable=True)

    # Preferences
    cuisines = db.Column(db.Text, nullable=True, default="[]")
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

        # Check if username OR email is already taken
        user_exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if user_exists:
            flash('Username or email already taken!', 'danger')
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
        username = request.form['username'].lower()  # Convert to lowercase
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')  # Flash success message
            return redirect(url_for('profile'))
        else:
            flash('Invalid credentials.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# =================== PROFILE PAGE ===================
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == "POST":
        # Update main user info
        current_user.username = request.form.get("username")
        current_user.email = request.form.get("email")
        current_user.bio = request.form.get("bio")

        if "profile_pic" in request.files:
            profile_pic = request.files["profile_pic"]
            if profile_pic and profile_pic.filename != "":
                filename = f"{current_user.id}_{secure_filename(profile_pic.filename)}"
                profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename

        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("profile"))

    members = current_user.members
    return render_template("profile.html", user=current_user, members=members)

@app.route('/add_member', methods=['POST'])
@login_required
def add_member():
    name = request.form.get('member_name')
    if name:
        new_member = Member(name=name, user_id=current_user.id)
        db.session.add(new_member)
        db.session.commit()
        flash(f"Added member: {name}", "success")
    return redirect(url_for('profile'))


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    if not check_password_hash(current_user.password, current_password):
        flash("Incorrect current password.", "danger")
        return redirect(url_for('profile'))

    if new_password != confirm_new_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for('profile'))

    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash("Password updated successfully!", "success")
    return redirect(url_for('profile'))

# =================== HOMEPAGE ===================
@app.route('/')
@login_required
def home():
    return render_template('index.html', user=current_user)

# =================== DIET CALCULATOR ===================
@app.route('/diet_calculator', methods=['GET', 'POST'])
@login_required
def diet_calculator():
    # Initialize variables to store diet info
    bmr = tdee = protein_grams = fat_grams = carbs_grams = None  # Default values

    if request.method == 'POST':
        print(f"Form data: {request.form}")  # Print all the form data
        
        weight = request.form.get('weight')
        if weight is None:
            flash("Weight is required.", "danger")
            return redirect(url_for('diet_calculator'))

        weight = float(weight)
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

        # # Debug print for calculations
        # print(f"Daily Calories: {tdee}")
        # print(f"Protein (grams): {protein_grams}")
        # print(f"Fat (grams): {fat_grams}")
        # print(f"Carbs (grams): {carbs_grams}")

        # Save the calculated values to the database (before 'Save to Profile')
        current_user.daily_calories = tdee
        current_user.protein_grams = protein_grams
        current_user.fat_grams = fat_grams
        current_user.carbs_grams = carbs_grams

        # Debug print for db
        print(f"Daily Calories: {current_user.daily_calories}")
        print(f"Protein (grams): {current_user.protein_grams}")
        print(f"Fat (grams): {current_user.fat_grams}")
        print(f"Carbs (grams): {current_user.carbs_grams}")


        try:
            print("Attempting to commit changes to the database...")  # Debugging line

            # Ensure changes are being tracked
            if db.session.dirty:
                print("Diet info calculated and saved to profile!")
                print("There are changes to commit.")
                db.session.flush()  # Ensure changes are written to the DB

            db.session.commit()
            flash("Diet info calculated and saved to profile!", "success")
        except Exception as e:
            print(f"Error during commit: {e}")  # This should show the error if it occurs
            flash(f"Error saving data: {e}", "danger")
            db.session.rollback()  # Rollback any changes if there's an error
            print(f"Error: {e}")  # Additional print for debugging
        
        # Now, handle the save to profile (the button click)
        if request.form.get("save_to_profile"):
            print(f"Save to profile button clicked!")

            member_id = request.form.get('member_id')
            if member_id:
                member = Member.query.filter_by(id=int(member_id), user_id=current_user.id).first()
                if member:
                    member.daily_calories = tdee
                    member.protein_grams = protein_grams
                    member.fat_grams = fat_grams
                    member.carbs_grams = carbs_grams
                    db.session.commit()
                    flash(f"Diet info saved for {member.name}!", "success")
            
            # Save the values from the database to user's profile
            try:
                # Get the latest values from the database (if needed)
                saved_tdee = current_user.daily_calories
                saved_protein = current_user.protein_grams
                saved_fat = current_user.fat_grams
                saved_carbs = current_user.carbs_grams

                # Commit changes to the database
                db.session.commit()

                flash("Diet info saved to profile!", "success")
            except Exception as e:
                flash(f"Error saving data: {e}", "danger")
                print(f"Error: {e}")

        # Render the result on the same page
        return render_template(
            'diet_calculator.html', 
            bmr=bmr, 
            tdee=tdee, 
            protein_grams=protein_grams, 
            fat_grams=fat_grams, 
            carbs_grams=carbs_grams
        )
    
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

# =================== RECIPES ===================
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import pandas as pd

# Assuming the path to your CSV is given correctly.
RECIPES_CSV_PATH = 'datasets/recipes_with_images.csv'
IMAGE_FOLDER_PATH = 'C:/Users/vae.tiolamon/Documents/DHBW Folder/DHBW 6. Semester/Food Images/Food Images/'

# Load CSV into DataFrame using pandas
def load_recipes():
    df = pd.read_csv(RECIPES_CSV_PATH)
    recipes = []
    for index, row in df.iterrows():
        recipe = {
            "name": row['Title'],
            "ingredients": row['Cleaned_Ingredients'].split(','), 
            "image": row['Image_Name']
        }
        recipes.append(recipe)
    return recipes

# Pre-load recipes into memory
recipes = load_recipes()

# Helper function to serve images
@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER_PATH, filename)

# Helper function to serve images
@app.route('/images/<filename>')
def send_image(filename):  # Renamed the function to avoid conflicts
    return send_from_directory(IMAGE_FOLDER_PATH, filename)

# Helper function for pagination
def paginate(items, page, per_page=9):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]

# Calculate page numbers to show (previous and next 3 pages, with ellipses)
def get_pagination_range(page, total_pages, num_links=3):
    pagination = []

    # Always show the first and last page
    if page > 1:
        pagination.append(1)  # First page
        if page > num_links + 1:
            pagination.append("...")  # Ellipsis for skipped pages

    # Calculate range of pages around current page
    start = max(page - num_links, 2)
    end = min(page + num_links, total_pages - 1)

    # Add pages around the current page
    pagination.extend(range(start, end + 1))

    # Always show the last page
    if page < total_pages:
        if page < total_pages - num_links - 1:
            pagination.append("...")  # Ellipsis for skipped pages
        pagination.append(total_pages)

    return pagination

@app.route('/recipe_lookup', methods=['GET', 'POST'])
@login_required
def recipe_lookup():
    search_results = []
    page = int(request.args.get('page', 1))  # Get the current page number from URL (default is 1)

    if request.method == 'POST':
        # Get user input
        ingredients_input = request.form.get('ingredients', '').split(',')
        name_input = request.form.get('recipe_name', '').lower()

        # Split the search input into individual words and filter out empty strings
        search_words = set(word.strip().lower() for word in (name_input + ' ' + ','.join(ingredients_input)).split() if word.strip())

        # Filter recipes by ingredients and name
        search_results = []
        for recipe in recipes:
            # Ensure recipe name is a string and handle missing/NaN values
            recipe_name = str(recipe['name']) if recipe['name'] else ""
            recipe_ingredients = [ingredient.strip().lower() for ingredient in recipe['ingredients']]

            # Check if all the words from the search input are in the recipe name or ingredients
            name_match = all(word in recipe_name.lower() for word in search_words)
            ingredient_match = all(word in recipe_ingredients for word in search_words)

            # Add the recipe to the results if it matches either the name or the ingredients
            if name_match or ingredient_match:
                search_results.append(recipe)

    # If no search terms, show all recipes, but paginated
    if not search_results:
        search_results = recipes

    # Paginate the results
    paginated_recipes = paginate(search_results, page)

    # Calculate total pages
    total_pages = len(search_results) // 9 + (1 if len(search_results) % 9 > 0 else 0)

    # Get pagination range
    pagination = get_pagination_range(page, total_pages)

    return render_template(
        'recipe_lookup.html', 
        search_results=paginated_recipes, 
        IMAGE_FOLDER_PATH=IMAGE_FOLDER_PATH,
        page=page,
        total_pages=total_pages,
        pagination=pagination
    )

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
