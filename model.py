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
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id',ondelete="CASCADE"), nullable=False)

    subject = db.relationship('Subject', backref=db.backref('chapters', lazy=True,cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Chapter(id={self.id}, name={self.name}, subject_id={self.subject_id})>"

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  

    chapter = db.relationship('Chapter', backref=db.backref('quizzes', lazy=True,cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Quiz(id={self.id}, chapter_id={self.chapter_id}, date={self.date})>"
        
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id',ondelete="CASCADE"), nullable=False)
    ques_statement = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct = db.Column(db.String(1), nullable=False)

    quiz = db.relationship('Quiz', backref=db.backref('questions', lazy=True,cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Question(id={self.id}, quiz_id={self.quiz_id})>"
        
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id',ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',ondelete="CASCADE"), nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score = db.Column(db.Float, nullable=False)

    quiz = db.relationship('Quiz', backref=db.backref('scores', lazy=True,cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('scores', lazy=True,cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Score(id={self.id}, quiz_id={self.quiz_id}, user_id={self.user_id}, score={self.score})>"

def create_test_data():
    if not User.query.filter_by(role="admin").first():
        admin = User(id=1, full_name="Admin", email="admin@example.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
    
    if not User.query.filter_by(email="shipra@example.com").first():
        user1 = User(id=2, full_name="Shipra", email="shipra@example.com")
        user1.set_password("password123")
        db.session.add(user1)
    
    if not User.query.filter_by(email="ships@example.com").first():
        user2 = User(id=3, full_name="Ships", email="ships@example.com")
        user2.set_password("password456")
        db.session.add(user2)
    
    if not Subject.query.first():
        subject1 = Subject(id=1, name="DBMS", description="Database Management Systems")
        subject2 = Subject(id=2, name="MAD-I", description="Modern Application Development - I")
        db.session.add_all([subject1, subject2])
    
    if not Chapter.query.first():
        chapter1 = Chapter(id=1, name="SQL", description="Structured Query Language", subject_id=1)
        chapter2 = Chapter(id=2, name="Normalization", description="DB Normalization", subject_id=1)
        chapter3 = Chapter(id=3, name="HTML", description="HyperText Markup Language", subject_id=2)
        chapter4 = Chapter(id=4, name="CSS", description="Cascading Style Sheets", subject_id=2)
        db.session.add_all([chapter1, chapter2, chapter3, chapter4])
    
    if not Quiz.query.first():
        quiz1 = Quiz(id=1, chapter_id=1, date=date.today(), duration=30)
        quiz2 = Quiz(id=2, chapter_id=3, date=date.today(), duration=45)
        db.session.add_all([quiz1, quiz2])
    
    if not Question.query.first():
        questions = [
            Question(quiz_id=1, ques_statement="What is SQL?", option_a="Programming Language", option_b="Query Language", option_c="Markup Language", option_d="Scripting Language", correct="B"),
            Question(quiz_id=1, ques_statement="What does DDL stand for?", option_a="Data Definition Language", option_b="Data Derivation Language", option_c="Database Design Language", option_d="None", correct="A"),
            Question(quiz_id=1, ques_statement="Which SQL clause is used to filter records?", option_a="SELECT", option_b="WHERE", option_c="ORDER BY", option_d="GROUP BY", correct="B"),
            Question(quiz_id=1, ques_statement="Which SQL statement is used to insert data?", option_a="INSERT INTO", option_b="ADD", option_c="MODIFY", option_d="APPEND", correct="A"),
            Question(quiz_id=1, ques_statement="Which key uniquely identifies a row in a table?", option_a="Foreign Key", option_b="Primary Key", option_c="Candidate Key", option_d="Super Key", correct="B"),
            Question(quiz_id=2, ques_statement="What is HTML?", option_a="Programming Language", option_b="Markup Language", option_c="Database", option_d="OS", correct="B"),
            Question(quiz_id=2, ques_statement="Which tag is used for hyperlinks?", option_a="<a>", option_b="<p>", option_c="<h1>", option_d="<div>", correct="A"),
            Question(quiz_id=2, ques_statement="Which attribute is used for images?", option_a="src", option_b="href", option_c="alt", option_d="title", correct="A"),
            Question(quiz_id=2, ques_statement="Which is the latest HTML version?", option_a="HTML4", option_b="HTML5", option_c="XHTML", option_d="HTML 3.2", correct="B"),
            Question(quiz_id=2, ques_statement="What does CSS stand for?", option_a="Cascading Style Sheets", option_b="Creative Style System", option_c="Computer Style Sheet", option_d="Colorful Style Sheets", correct="A"),
        ]
        db.session.add_all(questions)
    
    if not Score.query.first():
        scores = [
            Score(quiz_id=1, user_id=2, score=95.0, attempted_at=datetime.utcnow()),
            Score(quiz_id=1, user_id=3, score=97.0, attempted_at=datetime.utcnow()),
            Score(quiz_id=2, user_id=2, score=92.0, attempted_at=datetime.utcnow()),
            Score(quiz_id=2, user_id=3, score=94.0, attempted_at=datetime.utcnow()),
        ]
        db.session.add_all(scores)
    
    db.session.commit()
    print("Test data created successfully!")
