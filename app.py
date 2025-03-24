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

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)
login_manager.init_app(app)

app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(user, url_prefix="/user")

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
        return redirect(url_for('admin.admin_dashboard') if current_user.is_admin() else url_for('user.user_dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        dob = request.form.get('dob')
        education_level = request.form.get('education_level')
        qualifications = request.form.get('qualifications')
        institute_name = request.form.get('institute_name')
        field_of_study = request.form.get('field_of_study')

       
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email is already registered!", "danger")
            return redirect(url_for('register'))

      
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date() if dob else None

       
        new_user = User(
            full_name=full_name,
            email=email,
            dob=dob_date,
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
    app.run(debug=True) 