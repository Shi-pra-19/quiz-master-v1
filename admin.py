from flask import Blueprint, Flask, redirect, url_for, render_template, request, flash
from flask_login import login_user, login_required, current_user, logout_user
from extensions import db
from model import Subject, User, Chapter, Question, Quiz,Score
from sqlalchemy.orm import joinedload
from datetime import datetime
import plotly.graph_objs as go
import plotly.offline as pyo

admin = Blueprint("admin", __name__)


@admin.route('/home')
@login_required
def home():
    if not current_user.is_admin():
        return redirect(url_for('home'))

    subjects = Subject.query.options(
        joinedload(Subject.chapters)
        .joinedload(Chapter.quizzes)
        .joinedload(Quiz.questions)
    ).all()
    
    return render_template('admin_home.html', subjects=subjects)


@admin.route('/user')
@login_required
def user():
    if not current_user.is_admin():
        return redirect(url_for('home'))
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin_user.html', users=users)


@admin.route('/quiz')
@login_required
def quiz():
    if not current_user.is_admin():
        return redirect(url_for('home'))
    quizzes = Quiz.query.all()
    chapters = Chapter.query.all()
    return render_template('admin_quiz.html', quizzes=quizzes, chapters=chapters)

@admin.route('/search', methods=['GET'])
@login_required
def search():
    search_type = request.args.get('search_type', 'subject')  
    query = request.args.get('query', '').strip()
    
    results = []

    if query:
        if search_type == 'subject':
            results = db.session.query(Subject).filter(Subject.name.ilike(f"%{query}%")).all()
        elif search_type == 'quiz':
            results = db.session.query(Quiz).join(Chapter).join(Subject).filter(Quiz.chapter.has(Chapter.name.ilike(f"%{query}%"))).all()
        elif search_type == 'user':
            results = db.session.query(User).filter(
                (User.full_name.ilike(f"%{query}%")) | 
                (User.email.ilike(f"%{query}%"))
            ).all()
        elif search_type == 'question':
            results = db.session.query(Question).filter(Question.ques_statement.ilike(f"%{query}%")).all()

    return render_template('admin_search.html', search_type=search_type, query=query, results=results)


@admin.route('/summmary')
def summary():
    subjects = Subject.query.all()
    subject_names = [subject.name for subject in subjects]

    top_scores = []
    user_attempts = []

    for subject in subjects:
        quizzes = Quiz.query.join(Chapter).filter(Chapter.subject_id == subject.id).all()

        max_score = 0
        attempts = 0
        for quiz in quizzes:
            scores = Score.query.filter_by(quiz_id=quiz.id).all()
            if scores:
                max_score = max(max_score, max(score.score for score in scores))
                attempts += len(scores)

        top_scores.append(max_score)
        user_attempts.append(attempts)

    pastel_colors = ["#FAFFC7", "#ADD8E6"]

    score_fig = go.Figure()
    score_fig.add_trace(go.Bar(x=subject_names, y=top_scores, marker_color= pastel_colors[0], name="Top Scores"))
    score_fig.update_layout(title="Top Scores per Subject", xaxis_title="Subjects", yaxis_title="Top Score")

    
    attempts_fig = go.Figure()
    attempts_fig.add_trace(go.Bar(x=subject_names, y=user_attempts, marker_color=pastel_colors[1], name="User Attempts"))
    attempts_fig.update_layout(title="User Attempts per Subject", xaxis_title="Subjects", yaxis_title="Number of Attempts")

   
    score_plot_html = pyo.plot(score_fig, output_type="div")
    attempts_plot_html = pyo.plot(attempts_fig, output_type="div")

    return render_template('admin_summary.html', score_plot=score_plot_html, attempts_plot=attempts_plot_html)


@admin.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form.get('subject_name')
    subject_description = request.form.get('subject_description')

    if subject_name:
        new_subject = Subject(name=subject_name, description=subject_description)
        db.session.add(new_subject)
        db.session.commit()
        flash("Subject added successfully!", "success")
    
    return redirect(url_for('admin.home'))

@admin.route('/edit_subject/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    subject.name = request.form['subject_name']
    subject.description = request.form['subject_description']

    db.session.commit()
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('admin.home'))

@admin.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()

    flash("Subject deleted successfully!", "danger")
    return redirect(url_for('admin.home'))


@admin.route('/add_chapter/<int:subject_id>', methods=['POST'])
def add_chapter(subject_id):
    chapter_name = request.form.get('chapter_name')
    chapter_description = request.form.get('chapter_description')

    if not chapter_name or not chapter_description:
        flash("Both fields are required!", "danger")
        return redirect(url_for('admin.home'))

    new_chapter = Chapter(name=chapter_name, description=chapter_description, subject_id=subject_id)
    db.session.add(new_chapter)
    db.session.commit()

    flash("New chapter added successfully!", "success")
    return redirect(url_for('admin.home'))

@admin.route('/edit_chapter/<int:chapter_id>', methods=['POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    chapter.name = request.form['chapter_name']
    chapter.description = request.form['chapter_description']

    db.session.commit()
    flash("Chapter updated successfully!", "success")
    return redirect(url_for('admin.home'))

@admin.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()

    flash("Chapter deleted successfully!", "success")
    return redirect(url_for('admin.home'))

@admin.route('/add_quiz', methods=['POST'])
def add_quiz():
    new_quiz = Quiz(
        chapter_id=request.form.get('chapter_id'),
        date=datetime.strptime(request.form['date'], "%Y-%m-%d").date(),
        duration=request.form.get('duration'),
        remarks=request.form.get('remarks')
    )
    db.session.add(new_quiz)
    db.session.commit()

    flash('New quiz created successfully!', 'success')
    return redirect(url_for('admin.quiz'))

@admin.route('/edit_quiz/<int:quiz_id>', methods=['POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
    quiz.duration = request.form['duration']
    
    db.session.commit()
    flash("Quiz updated successfully!", "success")
    return redirect(url_for('admin.quiz'))

@admin.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()

    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('admin.quiz'))


@admin.route('/add_question/<int:quiz_id>', methods=['POST'])
def add_question(quiz_id):
    new_question = Question(
        quiz_id=quiz_id,
        ques_statement=request.form['ques_statement'],
        option_a=request.form['option_a'],
        option_b=request.form['option_b'],
        option_c=request.form['option_c'],
        option_d=request.form['option_d'],
        correct=request.form['correct']
    )
    
    db.session.add(new_question)
    db.session.commit()

    flash('New question added successfully!', 'success')
    return redirect(url_for('admin.quiz'))

@admin.route('/edit_question/<int:question_id>', methods=['POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    question.ques_statement = request.form['ques_statement']
    question.option_a = request.form['option_a']
    question.option_b = request.form['option_b']
    question.option_c = request.form['option_c']
    question.option_d = request.form['option_d']
    question.correct = request.form['correct']

    db.session.commit()
    flash('Question updated successfully!', 'success')
    return redirect(url_for('admin.quiz'))

@admin.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()

    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.quiz'))

