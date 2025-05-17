import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from models import db, User, Member, GroceryItem, MealPlan, Pantry
from forms import MemberForm
import urllib.parse

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mealplan.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'

db.init_app(app)

with app.app_context():
    db.create_all()

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# =================== AUTHENTICATION ===================

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify_password = request.form['verify_password']
        email = request.form['email']

        # Check if username OR email is already taken
        user_exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if user_exists:
            flash('Username or email already taken!', 'danger')
            return render_template('register.html', username=username, email=email)

        # Check if password and verify_password match
        if password != verify_password:
            flash('Passwords do not match! Please enter the same passwords', 'danger')
            return render_template('register.html', username=username, email=email)

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
        username = request.form['username'].lower()  
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')  
            return redirect(url_for('home'))
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
    members = Member.query.filter_by(user_id=current_user.id).all()
    selected_member_id = request.args.get('member_id')

    selected_member = None
    if selected_member_id:
        selected_member = Member.query.filter_by(id=selected_member_id, user_id=current_user.id).first()
    elif members:
        selected_member = members[0]

    # Parse JSON fields if present
    if selected_member:
        selected_member.cuisines = json.loads(selected_member.cuisines or "[]")
        selected_member.allergies = json.loads(selected_member.allergies or "[]")
        selected_member.dietary_restrictions = json.loads(selected_member.dietary_restrictions or "[]")

    # Handle updates
    if request.method == "POST" and selected_member:
        selected_member.name = request.form.get("member_name")
        selected_member.daily_calories = request.form.get("daily_calories")
        selected_member.protein_grams = request.form.get("protein_grams")
        selected_member.fat_grams = request.form.get("fat_grams")
        selected_member.carbs_grams = request.form.get("carbs_grams")
        selected_member.cuisines = str(request.form.getlist("cuisines[]"))
        selected_member.allergies = str(request.form.getlist("allergies[]"))
        selected_member.dietary_restrictions = str(request.form.getlist("dietary_restrictions[]"))
        db.session.commit()
        flash("Member updated!", "success")
        return redirect(url_for('profile', member_id=selected_member.id))

    form = MemberForm()

    return render_template(
        "profile.html",
        user=current_user,
        members=members,
        selected_member=selected_member,
        form=form 
    )

@app.route('/add_member', methods=['GET', 'POST'])
@login_required
def add_member():
    form = MemberForm()
    if request.method == 'POST':
        print("POST received")
        print("Form valid:", form.validate_on_submit())
        print("Errors:", form.errors)

    if form.validate_on_submit():
        member = Member(
            user_id=current_user.id,
            name=form.name.data,
            daily_calories=form.daily_calories.data,
            protein_grams=form.protein_grams.data,
            fat_grams=form.fat_grams.data,
            carbs_grams=form.carbs_grams.data,
            cuisines=json.dumps(form.cuisines.data),
            allergies=json.dumps(form.allergies.data),
            dietary_restrictions=json.dumps(form.dietary_restrictions.data)
        )
        db.session.add(member)
        db.session.commit()

        flash("Member added!")
        print("Members now:", Member.query.filter_by(user_id=current_user.id).all())
        return redirect(url_for('profile'))

    return render_template('add_member.html', form=form)

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
    bmr = tdee = protein_grams = fat_grams = carbs_grams = None 

    if request.method == 'POST':
        member_id = request.form.get('member_id')
        if member_id:
            member = Member.query.filter_by(id=member_id, user_id=current_user.id).first()
            if member:
                member.daily_calories = tdee
                member.protein_grams = protein_grams
                member.fat_grams = fat_grams
                member.carbs_grams = carbs_grams
                db.session.commit()
                flash(f"Diet info saved to {member.name}'s profile!", "success")
            else:
                flash("Member not found or unauthorized.", "danger")
                
        print(f"Form data: {request.form}") 

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
            print("Attempting to commit changes to the database...")  

            if db.session.dirty:
                print("Diet info calculated and saved to profile!")
                print("There are changes to commit.")
                db.session.flush()  

            db.session.commit()
            flash("Diet info calculated and saved to profile!", "success")
        except Exception as e:
            print(f"Error during commit: {e}") 
            flash(f"Error saving data: {e}", "danger")
            db.session.rollback()  
            print(f"Error: {e}")  

        if request.form.get("save_to_profile"):
            print(f"Save to profile button clicked!")

            
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
            carbs_grams=carbs_grams,
            user=current_user  # <-- Add this
        )

    return render_template('diet_calculator.html')

# =================== GROCERY LIST ===================
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
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
import pandas as pd
from PIL import Image
import io

RECIPES_CSV_PATH = 'datasets/recipes_with_images_and_nutrients.csv'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGE_FOLDER_PATH = os.path.join(BASE_DIR, 'Food Images')

# Load CSV into DataFrame using pandas
def load_recipes():
    df = pd.read_csv(RECIPES_CSV_PATH)
    recipes = []
    for index, row in df.iterrows():
        image_filename = row['Image_Name'].strip() + '.jpg'
        
        # Build relative image path for static folder
        image_path = os.path.join('static', 'food_images', image_filename) 
        
        # Check if the image exists inside the 'static/food_images' folder
        full_image_path = os.path.join(BASE_DIR, image_path)

        # print(full_image_path)
        
        if os.path.exists(full_image_path):
            image = image_filename
        else:
            image = 'default.jpg' 

        def split_instructions(text):
            if not isinstance(text, str):
                return []

            # Step 1: Replace special characters
            text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('\n', ' ')

            # Step 2: Protect common abbreviations
            abbreviations = {
                "tsp.": "tsp_placeholder",
                "tbsp.": "tbsp_placeholder",
                "oz.": "oz_placeholder",
                "fl. oz.": "floz_placeholder",
                "lb.": "lb_placeholder",
                "pt.": "pt_placeholder",
                "qt.": "qt_placeholder",
                "gal.": "gal_placeholder"
            }

            for abbr, placeholder in abbreviations.items():
                text = text.replace(abbr, placeholder)

            # Step 3: Split by sentence-ending punctuation followed by space
            steps = re.split(r'(?<=[.!?])\s+', text)

            # Step 4: Restore abbreviations and clean whitespace
            restored_steps = []
            for step in steps:
                for abbr, placeholder in abbreviations.items():
                    step = step.replace(placeholder, abbr)
                restored_steps.append(step.strip())

            return [s for s in restored_steps if s]
        
        import re
        import math

        def parse_nutrients(text):
            tuples = []
            pattern = r"\('([^']+)',\s*([^)]+)\)"

            for match in re.findall(pattern, text):
                key = match[0].strip()
                val_str = match[1].strip()
                try:
                    val = float(val_str)
                    if not math.isnan(val):
                        tuples.append((key, val))
                except ValueError:
                    continue  

            return tuples
        

        # Modify your recipe dict
        recipe = {
            "name": row['Title'],
            "calories": row['Calories'],
            "macro": parse_nutrients(row['Macro_Nutrients']),
            "micro": parse_nutrients(row['Micro_Nutrients']),
            "ingredients": [ing.strip().replace('\n', ' ') for ing in row['Cleaned_Ingredients'].split(',')],
            "instructions": split_instructions(row['Instructions']),
            "image": image
        }

        recipes.append(recipe)
        # print(f"Checking: {full_image_path} -> {os.path.exists(full_image_path)}")

    return recipes

# Pre-load recipes into memory
recipes = load_recipes()

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

# Add to your imports if not already present
from flask import jsonify, request
from flask_login import login_required
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re, time, requests

# --- Ingredient matching dictionaries ---

# Specific ingredients — prioritized exact matches
SPECIFIC_INGREDIENTS = {
    "duck eggs": ["duck eggs", "salted duck eggs", "fermented duck eggs"],
    "oyster sauce": ["oyster sauce", "premium oyster sauce", "vegetarian oyster sauce"],
    "soy milk": ["soy milk", "unsweetened soy milk", "sweetened soy milk", "organic soy milk"],
    "quail eggs": ["quail eggs", "boiled quail eggs"],
    "coconut milk": ["coconut milk", "organic coconut milk", "light coconut milk"],
    "almond milk": ["almond milk", "unsweetened almond milk", "vanilla almond milk"],
    "evaporated milk": ["evaporated milk"],
    "condensed milk": ["condensed milk", "sweetened condensed milk"],
    "fish sauce": ["fish sauce", "premium fish sauce", "thai fish sauce"],
    "hoisin sauce": ["hoisin sauce"],
    "rice vinegar": ["rice vinegar", "seasoned rice vinegar"],
    "apple cider vinegar": ["apple cider vinegar"],
}

# Broad categories with common variants
MAIN_INGREDIENT_PATTERNS = {
    "chicken": [
        "chicken breast", "chicken thigh", "grilled chicken", "roast chicken",
        "whole chicken", "baked chicken", "fried chicken", "boiled chicken",
        "chicken leg", "chicken drumstick", "shredded chicken", "chicken wing"
    ],
    "beef": [
        "ground beef", "beef steak", "roast beef", "beef strips",
        "braised beef", "beef ribs", "beef brisket", "beef patty"
    ],
    "fish": [
        "grilled fish", "salmon", "cod", "tuna", "mackerel", "tilapia",
        "baked fish", "pan-fried fish", "steamed fish", "fish fillet"
    ],
    "shrimp": [
        "grilled shrimp", "shrimp skewer", "boiled shrimp", "fried shrimp",
        "shrimp cocktail", "shrimp tempura", "peeled shrimp"
    ],
    "tofu": [
        "tofu", "firm tofu", "silken tofu", "fried tofu", "grilled tofu", "tofu cubes"
    ],
    "lentils": [
        "lentils", "red lentils", "green lentils", "brown lentils", "yellow lentils", "split lentils"
    ],
    "pork": [
        "pork chop", "pork loin", "ground pork", "roast pork", "bbq pork", 
        "pork belly", "braised pork", "fried pork", "pork ribs"
    ]
}

# Exclusions to prevent false matches
EXCLUDED_INGREDIENT_PATTERNS = {
    "chicken": [
        "chicken broth", "chicken stock", "egg", "chicken egg", "chicken bouillon",
        "cream of chicken soup", "dried chicken powder"
    ],
    "beef": [
        "beef broth", "beef stock", "beef bouillon", "cream of beef soup"
    ],
    "fish": [
        "fish sauce", "fish paste", "anchovy paste"
    ],
    "shrimp": [
        "shrimp paste", "dried shrimp powder", "shrimp seasoning"
    ],
    "pork": [
        "pork broth", "bacon bits", "pork flavoring", "pork stock"
    ],
    # These are exact-match ingredients, so no exclusion needed
    "duck eggs": [],
    "oyster sauce": [],
    "soy milk": [],
    "quail eggs": [],
    "coconut milk": [],
    "almond milk": [],
    "evaporated milk": [],
    "condensed milk": [],
    "fish sauce": [],
    "hoisin sauce": [],
    "rice vinegar": [],
    "apple cider vinegar": [],
}

# --- Helper Functions ---

def extract_main_ingredient(prompt):
    prompt = prompt.lower()

    # First, prevent false matches by checking exclusions
    for general in EXCLUDED_INGREDIENT_PATTERNS:
        for exclusion in EXCLUDED_INGREDIENT_PATTERNS[general]:
            if re.search(rf"\b{re.escape(exclusion)}\b", prompt):
                return None  # Detected an excluded phrase

    # Next, look for specific ingredients (like duck eggs, soy milk)
    for specific in SPECIFIC_INGREDIENTS:
        if re.search(rf"\b{re.escape(specific)}\b", prompt):
            return specific

    # Finally, fallback to general ingredient matches
    for general in MAIN_INGREDIENT_PATTERNS:
        if re.search(rf"\b{general}\b", prompt):
            return general

    return None

def extract_calorie_limit(prompt):
    match = re.search(r"under (\d+)", prompt)
    return int(match.group(1)) if match else None

def is_main_ingredient_match(ingredient, ingredients_list):
    """Check if recipe ingredients include allowed ingredient and exclude false matches."""
    text = " ".join(ingredients_list).lower()

    if ingredient in SPECIFIC_INGREDIENTS:
        allowed = any(p in text for p in SPECIFIC_INGREDIENTS[ingredient])
        return allowed

    # General category match
    allowed = any(p in text for p in MAIN_INGREDIENT_PATTERNS.get(ingredient, [ingredient]))
    excluded = any(p in text for p in EXCLUDED_INGREDIENT_PATTERNS.get(ingredient, []))
    return allowed and not excluded

# --- Route ---

@app.route('/chatbot-recommend', methods=['POST'])
@login_required
def chatbot_recommend():
    start_time = time.time()

    data = request.get_json()
    prompt = data.get("prompt", "").lower()

    if not prompt:
        return jsonify({"recipes": []})

    calorie_limit = extract_calorie_limit(prompt)
    main_ingredient = extract_main_ingredient(prompt)

    documents = [
        str(r.get("name", "")) + " " + " ".join(r.get("ingredients", []))
        for r in recipes
    ]
    vectorizer = TfidfVectorizer().fit(documents + [prompt])
    doc_vectors = vectorizer.transform(documents)
    prompt_vector = vectorizer.transform([prompt])

    similarities = cosine_similarity(prompt_vector, doc_vectors).flatten()
    top_indices = similarities.argsort()[-10:][::-1]
    top_recipes = [recipes[i] for i in top_indices]

    if calorie_limit:
        top_recipes = [r for r in top_recipes if r.get("calories", 99999) <= calorie_limit]

    if main_ingredient:
        top_recipes = [
            r for r in top_recipes
            if is_main_ingredient_match(main_ingredient, r.get("ingredients", []))
        ]

    if not top_recipes:
        return jsonify({"recipes": []})

    context = "\n".join([
        f"- {r['name']} (Calories: {r['calories']}) - Ingredients: {', '.join(r['ingredients'])}"
        for r in top_recipes
    ])

    full_prompt = f"""
I have the following recipes:
{context}

Based on the user request: "{prompt}", which recipes would you recommend and why?
Please return up to 3 suggestions.
"""

    llama_start = time.time()
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": full_prompt, "stream": False}
        )
        result = response.json()
        llama_output = result.get("response", "").strip()
    except Exception as e:
        print("❌ LLaMA error:", e)
        llama_output = "Sorry, the model failed to respond."
    llama_end = time.time()

    print(f"⏱️ Total time: {time.time() - start_time:.2f}s | LLaMA time: {llama_end - llama_start:.2f}s")
    print("📨 Full prompt sent to LLaMA:\n", full_prompt)

    return jsonify({
        "response": llama_output,
        "recipes": [
            {
                "name": r["name"],
                "calories": r["calories"],
                "image": r["image"]
            } for r in top_recipes
        ]
    })


from flask import request

@app.route('/recipe_lookup/<recipe_name>')
def recipe_detail(recipe_name):
    decoded_name = urllib.parse.unquote(recipe_name)
    source = request.args.get("source")
    prompt = request.args.get("prompt")

    recipes = load_recipes()
    recipe = next((r for r in recipes if r["name"] == decoded_name), None)

    if recipe is None:
        return "Recipe not found", 404

    return render_template('recipe_detail.html', recipe=recipe, source=source, prompt=prompt)


@app.route('/save_to_meal_planner', methods=['POST'])
@login_required
def save_to_meal_planner():
    recipe_name = request.form['recipe_name']
    recipe_calories = request.form['recipe_calories']
    recipe_macro = request.form['recipe_macro']
    recipe_micro = request.form['recipe_micro']
    meal = request.form['meal']
    date_str = request.form['date']

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format", "danger")
        return redirect(url_for('recipe_lookup'))

    existing = MealPlan.query.filter_by(user_id=current_user.id, date=date, meal_type=meal).first()
    if existing:
        existing.recipe_name = recipe_name
        existing.recipe_calories = recipe_calories
        existing.recipe_macro = recipe_macro
        existing.recipe_micro = recipe_micro
        flash(f"{meal.capitalize()} on {date} updated.", "success")
    else:
        new_entry = MealPlan(
            user_id=current_user.id,
            date=date,
            meal_type=meal,
            recipe_name=recipe_name,
            recipe_calories=recipe_calories,
            recipe_macro=recipe_macro,
            recipe_micro=recipe_micro
        )
        db.session.add(new_entry)
        flash(f"{meal.capitalize()} on {date} added.", "success")

    db.session.commit()
    return redirect(url_for('meal_planner'))


# =================== MEAL PLANNER ===================
@app.route('/meal_planner')
@login_required
def meal_planner():
    week_param = request.args.get("week")  # e.g., '2025-W19'

    if week_param:
        try:
            year, week_num = map(int, week_param.split("-W"))
            start_of_week = datetime.fromisocalendar(year, week_num, 1).date()
            end_of_week = start_of_week + timedelta(days=6)
        except Exception:
            start_of_week = None
            end_of_week = None
    else:
        today = datetime.today().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        week_param = f"{start_of_week.isocalendar()[0]}-W{start_of_week.isocalendar()[1]}"

    meals = MealPlan.query.filter(
        MealPlan.user_id == current_user.id,
        MealPlan.date >= start_of_week,
        MealPlan.date <= end_of_week
    ).all()

    meal_data = {}
    for meal in meals:
        weekday = meal.date.strftime('%A').lower()
        key_by_day = f"{weekday}_{meal.meal_type}"
        key_by_date = f"{meal.date}_{meal.meal_type}"

        meal_data[key_by_day] = {
            'name': meal.recipe_name,
            'calories': meal.recipe_calories,
            'macro': meal.recipe_macro,
            'micro': meal.recipe_micro
        }

        meal_data[key_by_date] = meal_data[key_by_day]  


    return render_template(
        "meal_planner.html",
        meal_data=meal_data,
        selected_week=week_param,
        start_of_week=start_of_week,
        timedelta=timedelta 
    )

# =================== PANTRY ORGANIZATION ===================
from flask import request, jsonify
import os
import pytesseract
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 

# lookup opencv barcode recognition

UPLOAD_FOLDER = 'static/uploads/ocr'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def preprocess_image_for_barcode(img):
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    contrast = clahe.apply(gray)

    # Sharpen image with a kernel
    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(contrast, -1, kernel)

    return sharpened

def extract_barcode_and_text(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    print("Image loaded successfully.")

    processed_img = preprocess_image_for_barcode(img)

    # Save processed image to debug
    cv2.imwrite('debug_processed.jpg', processed_img)

    barcodes = decode(processed_img)
    print(f"Barcodes found after preprocessing: {len(barcodes)}")

    results = []

    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        print(f"Barcode data: {barcode_data}")

        x, y, w, h = barcode.rect

        ocr_region_y_start = y + h
        ocr_region_y_end = ocr_region_y_start + int(h * 0.5)
        ocr_region = img[ocr_region_y_start:ocr_region_y_end, x:x+w]

        ocr_pil = Image.fromarray(cv2.cvtColor(ocr_region, cv2.COLOR_BGR2RGB))
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        ocr_text = pytesseract.image_to_string(ocr_pil, config=custom_config).strip()

        print(f"OCR extracted digits below barcode: '{ocr_text}'")

        results.append({
            'barcode_data': barcode_data,
            'ocr_text_below_barcode': ocr_text
        })

    if not results:
        print("No barcodes detected.")
    return results

@app.route('/scan_barcode', methods=['POST'])
@login_required
def scan_barcode():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        results = extract_barcode_and_text(filepath)
        if not results:
            return jsonify({'message': 'No barcodes detected'}), 200
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/pantry', methods=['GET', 'POST'])
@login_required
def pantry():
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        name = request.form['item']
        quantity = int(request.form['quantity'])
        expiration_str = request.form['expiration']
        expiration_date = datetime.strptime(expiration_str, '%Y-%m-%d').date()

        if item_id:
            pantry_item = Pantry.query.get(int(item_id))
            if pantry_item and pantry_item.user_id == current_user.id:
                pantry_item.name = name
                pantry_item.quantity = quantity
                pantry_item.expired = expiration_date
                pantry_item.selected = 'selected' in request.form
                db.session.commit()
                flash('Pantry item updated successfully.', 'success')
        else:
            new_item = Pantry(
                name=name,
                quantity=quantity,
                expired=expiration_date,
                selected='selected' in request.form,
                user_id=current_user.id
            )
            db.session.add(new_item)
            db.session.commit()
            flash('Pantry item added!', 'success')

        return redirect(url_for('pantry'))

    items = Pantry.query.filter_by(user_id=current_user.id).all()
    return render_template('pantry.html', items=items)

# ------------------ INIT DB ------------------ #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
