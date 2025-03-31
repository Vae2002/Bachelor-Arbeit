from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

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
    return render_template('grocery_list.html', items=items)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists! Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(username=username, password=password)
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
        if user and user.password == password:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('grocery'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


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

# Update item name and quantity
@app.route('/rename/<int:item_id>', methods=['POST'])
@login_required
def rename_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    new_name = request.form.get('new_name')
    new_quantity = request.form.get('new_quantity')

    # Update the item's name and quantity in the database
    if new_name and new_quantity:
        item.name = new_name
        item.quantity = int(new_quantity)
        db.session.commit()

    return '', 200  # Return a success response

# Toggle item purchased status (for the radio button)
@app.route('/toggle_purchased/<int:item_id>', methods=['POST'])
@login_required
def toggle_purchased(item_id):
    # Find the item by ID
    item = GroceryItem.query.get_or_404(item_id)
    
    # Toggle the purchased status
    item.purchased = not item.purchased
    db.session.commit()

    # Return the new purchased status in the response
    return {'purchased': item.purchased}, 200


# Clear all purchased items
@app.route('/clear_all', methods=['POST'])
@login_required
def clear_all():
    # Delete all purchased items from the database
    items_to_delete = GroceryItem.query.filter_by(purchased=True).all()
    for item in items_to_delete:
        db.session.delete(item)
    db.session.commit()

    return {'message': 'All purchased items have been cleared.'}, 200

@app.route('/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = GroceryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('grocery'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
