from extensions import db, login_manager
from config import Config
from model import create_test_data, User
from flask import Flask
from flask_login import login_user, login_required, current_user, logout_user
from flask import Flask, redirect, url_for, render_template, request, flash
from werkzeug.security import check_password_hash
from datetime import datetime
from admin import admin
from user import user
from api import api_bp
import os 

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)
login_manager.init_app(app)

app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(user, url_prefix="/user")
app.register_blueprint(api_bp, url_prefix="/api")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for('admin.home'))
        elif current_user.role == "user":
            return redirect(url_for('user.home'))
    
    return render_template('home.html')
    


@app.route('/register', methods=['GET', 'POST'])
def register():
   
    if current_user.is_authenticated:
        return redirect(url_for('admin.home') if current_user.is_admin() else url_for('user.home'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        dob_str = request.form.get('dob')
        education_level = request.form.get('education_level')
        qualifications = request.form.get('qualifications')
        institute_name = request.form.get('institute_name')
        field_of_study = request.form.get('field_of_study')

        if not full_name or not email or not password or not confirm_password:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        if not all(c.isalpha() or c.isspace() for c in full_name):
            flash("Full name should contain only letters and spaces!", "danger")
            return redirect(url_for('register'))

        if "@" not in email or "." not in email:
            flash("Invalid email format!", "danger")
            return redirect(url_for('register'))

        if len(password) < 8:
            flash("Password must be at least 8 characters long!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email is already registered!", "danger")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None

        new_user = User(
            full_name=full_name,
            email=email,
            dob=dob,
            education_level=education_level,
            qualifications=qualifications,
            institute_name=institute_name,
            field_of_study=field_of_study,
            role="user" 
        )
        new_user.set_password(password) 

        db.session.add(new_user)
        db.session.commit()

      
        login_user(new_user)

      
        return redirect(url_for('user.home'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for('admin.home'))
        elif current_user.role == "user":
            return redirect(url_for('user.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

       
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)  

           
            if user.role == "admin":
                return redirect(url_for('admin.home'))
            elif user.role == "user":
                return redirect(url_for('user.home'))
        else:
            flash("Invalid email or password", "danger")  

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  
    return redirect(url_for('home'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
        create_test_data()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)