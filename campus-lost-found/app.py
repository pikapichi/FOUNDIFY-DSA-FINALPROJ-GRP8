from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from data_structures import LostAndFoundMatcher
from models import db, bcrypt, User, LostItem, FoundItem

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_and_found.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)

# Initialize the DSA system (for matching algorithm)
matcher = LostAndFoundMatcher()

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Create database tables
with app.app_context():
    db.create_all()
    
    # Create default admin user if doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', name='Admin User', email='admin@campus.edu')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created (username: admin, password: admin123)")


@app.route('/')
def home():
    """Home page"""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user.id
            session['name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
        else:
            # Create new user
            user = User(username=username, name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/lost')
def lost_items():
    """Display all lost items"""
    items = LostItem.query.order_by(LostItem.created_at.desc()).all()
    categories = db.session.query(LostItem.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('lost_items.html', items=items, categories=categories)


@app.route('/found')
def found_items():
    """Display all found items"""
    items = FoundItem.query.order_by(FoundItem.created_at.desc()).all()
    categories = db.session.query(FoundItem.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('found_items.html', items=items, categories=categories)

@app.route('/report-lost', methods=['GET', 'POST'])
def report_lost():
    """Report a lost item"""
    if 'logged_in' not in session:
        flash('Please login to report a lost item', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('desc')
        category = request.form.get('category')
        location = request.form.get('location')
        date = request.form.get('date')
        user_id = session.get('user_id')
        
        # Handle file upload
        photo = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo = filename
        
        # Generate item ID
        count = LostItem.query.count() + 1
        item_id = f"L{count:03d}"
        
        # Create database entry
        lost_item = LostItem(
            item_id=item_id,
            name=name,
            desc=desc,
            category=category,
            location=location,
            date=date,
            photo=photo,
            user_id=user_id
        )
        db.session.add(lost_item)
        db.session.commit()
        
        flash(f'Lost item {item_id} reported successfully!', 'success')
        return redirect(url_for('lost_items'))
    
    return render_template('report_lost.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/report-found', methods=['GET', 'POST'])
def report_found():
    """Report a found item"""
    if 'logged_in' not in session:
        flash('Please login to report a found item', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('desc')
        category = request.form.get('category')
        location = request.form.get('location')
        date = request.form.get('date')
        user_id = session.get('user_id')
        
        # Handle file upload
        photo = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo = filename
        
        # Generate item ID
        count = FoundItem.query.count() + 1
        item_id = f"F{count:03d}"
        
        # Create database entry
        found_item = FoundItem(
            item_id=item_id,
            name=name,
            desc=desc,
            category=category,
            location=location,
            date=date,
            photo=photo,
            user_id=user_id
        )
        db.session.add(found_item)
        db.session.commit()
        
        flash(f'Found item {item_id} reported successfully!', 'success')
        return redirect(url_for('found_items'))
    
    return render_template('report_found.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/matches/<item_id>/<item_type>')
def view_matches(item_id, item_type):
    """View matches for an item"""
    is_lost = (item_type == 'lost')
    
    # Get the original item from DATABASE
    if is_lost:
        item = LostItem.query.filter_by(item_id=item_id).first()
    else:
        item = FoundItem.query.filter_by(item_id=item_id).first()
    
    # Check if item exists
    if not item:
        flash('Item not found. Please try again.', 'error')
        if is_lost:
            return redirect(url_for('lost_items'))
        else:
            return redirect(url_for('found_items'))
    
    # Get opposite items for matching
    if is_lost:
        target_items = FoundItem.query.all()
    else:
        target_items = LostItem.query.all()
    
    # Calculate matches
    matches = []
    for target_item in target_items:
        # Calculate similarity score
        score = 0
        
        # Name similarity (40%)
        from difflib import SequenceMatcher
        name_sim = SequenceMatcher(None, item.name.lower(), target_item.name.lower()).ratio()
        score += name_sim * 40
        
        # Description similarity (20%)
        desc_sim = SequenceMatcher(None, item.desc.lower(), target_item.desc.lower()).ratio()
        score += desc_sim * 20
        
        # Category match (20%)
        if item.category.lower() == target_item.category.lower():
            score += 20
        
        # Location match (15%)
        if item.location.lower() == target_item.location.lower():
            score += 15
        
        # Date proximity (5%)
        try:
            from datetime import datetime
            date1 = datetime.strptime(item.date, '%Y-%m-%d')
            date2 = datetime.strptime(target_item.date, '%Y-%m-%d')
            days_diff = abs((date1 - date2).days)
            if days_diff <= 7:
                score += 5 * (1 - days_diff / 7)
        except:
            pass
        
        # Add to matches if score is above threshold
        if score >= 30:
            matches.append({
                'item': target_item,
                'score': int(score)
            })
    
    # Sort by score descending
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('matches.html', 
                         item=item, 
                         matches=matches[:10],  # Top 10 matches
                         item_type=item_type)

@app.route('/api/autocomplete')
def autocomplete():
    """API endpoint for autocomplete"""
    prefix = request.args.get('prefix', '')
    item_type = request.args.get('type', 'lost')
    
    suggestions = matcher.get_autocomplete_suggestions(prefix, item_type)
    return jsonify(suggestions)

@app.route('/profile')
def profile():
    """User profile page"""
    if 'logged_in' not in session:
        flash('Please login to view profile', 'error')
        return redirect(url_for('login'))
    
    # Get user from database
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    # Get user's lost and found items
    user_lost_items = LostItem.query.filter_by(user_id=user_id).all()
    user_found_items = FoundItem.query.filter_by(user_id=user_id).all()
    
    return render_template('profile.html', 
                         user=user,
                         lost_items=user_lost_items,
                         found_items=user_found_items)

@app.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)


