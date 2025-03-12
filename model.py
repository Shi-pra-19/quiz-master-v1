from flask_sqlalchemy import SQLAlchemy
from extensions import db
from datetime import datetime,timezone,date,time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dob = db.Column(db.Date, nullable=True)
    education_level = db.Column(db.String(50), nullable=True)
    qualifications = db.Column(db.String(255), nullable=True)
    institute_name = db.Column(db.String(100), nullable=True)
    field_of_study = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(10), nullable=False, default="user") 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name}, role={self.role})>"


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Subject(id={self.id}, name={self.name})>"

class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)

    subject = db.relationship('Subject', backref=db.backref('chapters', lazy=True))

    def __repr__(self):
        return f"<Chapter(id={self.id}, name={self.name}, subject_id={self.subject_id})>"

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  
    remarks = db.Column(db.Text, nullable=True)

    chapter = db.relationship('Chapter', backref=db.backref('quizzes', lazy=True))

    def __repr__(self):
        return f"<Quiz(id={self.id}, chapter_id={self.chapter_id}, date={self.date})>"
        
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    ques_statement = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct = db.Column(db.String(1), nullable=False)

    quiz = db.relationship('Quiz', backref=db.backref('questions', lazy=True))

    def __repr__(self):
        return f"<Question(id={self.id}, quiz_id={self.quiz_id})>"
        
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score = db.Column(db.Float, nullable=False)

    quiz = db.relationship('Quiz', backref=db.backref('scores', lazy=True))
    user = db.relationship('User', backref=db.backref('scores', lazy=True))

    def __repr__(self):
        return f"<Score(id={self.id}, quiz_id={self.quiz_id}, user_id={self.user_id}, score={self.score})>"

def create_test_data():

   
    if not User.query.filter_by(role="admin").first():
        admin = User(id = 1,full_name="admin", email="admin@example.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

   
    if not User.query.filter_by(role="user").first():
        user = User(
            id = 2, full_name="Shipra", email="shipra@example.com")
        user.set_password("password123")
        
       
        db.session.add(user)

   
    if not Subject.query.first():
        subject1 = Subject(id=1, name="DBMS", description="Database Management Systems")
        subject2 = Subject(id=2, name="MAD-I", description="Modern Application Development - I")
        db.session.add_all([subject1, subject2])
    
   
    if not Chapter.query.first():
        chapter1 = Chapter(id=1,name="SQL", description="Structured Query Language", subject_id=1)
        chapter2 = Chapter(id=2,name="HTML", description="HyperText Markup Language", subject_id=2)
        db.session.add_all([chapter1, chapter2])
    
  
    if not Quiz.query.first():
        quiz1 = Quiz(id=1,chapter_id=1, date=date.today(), duration=30, remarks="Quiz for SQL Chapter")
        quiz2 = Quiz(id=2,chapter_id=2, date=date.today(), duration=45, remarks="Quiz for HTML Chapter")
        db.session.add_all([quiz1, quiz2])

   
    if not Question.query.first():
        question1 = Question(
            quiz_id=1, ques_statement="What is SQL?", option_a="Programming Language",
            option_b="Query Language", option_c="Markup Language", option_d="Scripting Language", correct="B"
        )
        question2 = Question(
            quiz_id=2, ques_statement="What is HTML?", option_a="Programming Language",
            option_b="Markup Language", option_c="Database", option_d="OS", correct="B"
        )
        db.session.add_all([question1, question2])

   
    if not Score.query.first():
        score1 = Score(quiz_id=1, user_id=2, score=93.0,attempted_at=datetime.utcnow())
        score2 = Score(quiz_id=2, user_id=2, score=90.0,attempted_at=datetime.utcnow())
        db.session.add_all([score1, score2])

   
    db.session.commit()
    print("Test data created successfully!")