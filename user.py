from flask_login import login_user, login_required, current_user, logout_user
from flask import Flask, redirect, url_for, render_template, request, flash,session, Blueprint
from model import Subject, Quiz, Score, Chapter, Question
from datetime import date, datetime, timedelta
from extensions import db
from collections import defaultdict
from sqlalchemy.sql import func
import plotly.graph_objs as go
import plotly.offline as pyo

user = Blueprint("user", __name__)

@user.route('/home')
@login_required
def home():
    today = date.today()
    quizzes = Quiz.query.filter(Quiz.date >= today).order_by(Quiz.date).all()
    past_quizzes = Quiz.query.filter(Quiz.date < today).order_by(Quiz.date.desc()).all()
    return render_template('user_home.html', quizzes=quizzes, past_quizzes=past_quizzes,today=today)


@user.route('/subject')
@login_required
def subject():
    subjects = Subject.query.all()
    return render_template('user_subject.html', subjects = subjects)


@user.route('/search', methods=['GET'])
@login_required
def search():
    search_type = request.args.get('search_type', 'subject')  # Default to 'subject'
    query = request.args.get('query', '').strip()

    results = []

    if query:
        if search_type == 'subject':
            results = db.session.query(Subject).filter(Subject.name.ilike(f"%{query}%")).all()
        elif search_type == 'quiz':
            results = db.session.query(Quiz).join(Chapter).join(Subject).filter(Quiz.chapter.has(Chapter.name.ilike(f"%{query}%"))).all()

    return render_template('user_search.html', search_type=search_type, query=query, results=results)



@user.route('/scores')
@login_required
def scores():
    scores = (
        db.session.query(Score, Quiz, Chapter)
        .join(Quiz, Score.quiz_id == Quiz.id)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .filter(Score.user_id == current_user.id)
        .order_by(Score.attempted_at.desc()) 
        .all()
    )
    
    highest_score = (
        db.session.query(func.max(Score.score), Quiz, Chapter)
        .join(Quiz, Score.quiz_id == Quiz.id)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .filter(Score.user_id == current_user.id)
        .first()
    )
    
    highest_score_value = highest_score[0] if highest_score[0] else 0
    highest_quiz_name = highest_score[2].name if highest_score[2] else "None"

   
    avg_score = db.session.query(func.avg(Score.score)).filter(Score.user_id == current_user.id).scalar() or 0
    avg_score = round(avg_score, 2)

    
    total_attempts = db.session.query(func.count(Score.id)).filter(Score.user_id == current_user.id).scalar() or 0
    total_quizzes = db.session.query(func.count(Quiz.id)).filter(Quiz.id.in_([s.quiz_id for s, _, _ in scores])).scalar() or 1
    avg_attempts_per_quiz = round(total_attempts / total_quizzes, 2)

    return render_template('user_scores.html', scores=scores,highest_score=highest_score_value,
        highest_quiz_name=highest_quiz_name,
        avg_score=avg_score,
        avg_attempts_per_quiz=avg_attempts_per_quiz)


@user.route('/summary')
def summary():
    user_id = current_user.id  
    subjects = Subject.query.all()
    subject_names = [subject.name for subject in subjects]

    num_quizzes = []
    top_scores = []

    for subject in subjects:
        quizzes = Quiz.query.join(Chapter).filter(Chapter.subject_id == subject.id).all()
        num_quizzes.append(len(quizzes)) 

       
        user_scores = []
        for quiz in quizzes:
            score = Score.query.filter_by(quiz_id=quiz.id, user_id=user_id).order_by(Score.score.desc()).first()
            if score:
                user_scores.append(score.score)

        top_scores.append(max(user_scores) if user_scores else 0)

    
    pastel_colors = ["#FAFFC7", "#ADD8E6"] 
    
    quiz_fig = go.Figure()
    quiz_fig.add_trace(go.Bar(
        x=subject_names,
        y=num_quizzes,
        marker_color=pastel_colors[0],  
        name="No. of Quizzes"
    ))
    quiz_fig.update_layout(title="Number of Quizzes per Subject", xaxis_title="Subjects", yaxis_title="No. of Quizzes")

    
    score_fig = go.Figure()
    score_fig.add_trace(go.Bar(
        x=subject_names,
        y=top_scores,
        marker_color=pastel_colors[1],  
        name="Top Scores"
    ))
    score_fig.update_layout(title="Your Top Scores per Subject", xaxis_title="Subjects", yaxis_title="Top Score")

   
    quiz_plot_html = pyo.plot(quiz_fig, output_type="div")
    score_plot_html = pyo.plot(score_fig, output_type="div")

    return render_template('user_summary.html', quiz_plot=quiz_plot_html, score_plot=score_plot_html)

@user.route('/start_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if 'quiz_start_time' not in session or session.get('current_quiz_id') != quiz_id:
        session['quiz_start_time'] = datetime.utcnow().isoformat()
        session['current_quiz_id'] = quiz_id  

   
    if request.method == 'GET':
        return render_template('start_quiz.html', quiz=quiz)

   
    start_time = datetime.fromisoformat(session['quiz_start_time'])
    end_time = start_time + timedelta(minutes=quiz.duration)
    is_time_up = datetime.utcnow() > end_time

    
    score = 0
    total = len(quiz.questions)
    user_answers = {}

    for question in quiz.questions:
        selected_answer = request.form.get(str(question.id)) if not is_time_up else None
        user_answers[str(question.id)] = selected_answer
        if selected_answer == question.correct:
            score += 1

    percentage = (score / total) * 100 if total > 0 else 0
    if is_time_up:
        percentage = 0  

   
    new_score = Score(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=percentage,
        attempted_at=datetime.utcnow()
    )
    db.session.add(new_score)
    db.session.commit()

   
    session.pop('quiz_start_time', None)
    session.pop('current_quiz_id', None)

    session['quiz_results'] = {
        'score': score,
        'total': total,
        'user_answers': user_answers
    }

    if is_time_up:
        flash("Time's up! Your quiz was automatically submitted.", "warning")

    return redirect(url_for('user.quiz_result', quiz_id=quiz.id))

@user.route('/quiz_result/<int:quiz_id>')
@login_required
def quiz_result(quiz_id):
   
    quiz_data = session.get('quiz_results', {})
    
    score = quiz_data.get('score', 0)
    total = quiz_data.get('total', 0)
    user_answers = quiz_data.get('user_answers', {})

   
    quiz_questions = Question.query.filter_by(quiz_id=quiz_id).all()
    correct_count = 0 
    question_results = []
    
    for question in quiz_questions:
        user_answer = user_answers.get(str(question.id), "Not Answered")
        is_correct = user_answer == question.correct
        
        if is_correct:
            correct_count += 1  


        question_results.append({
            "ques_statement": question.ques_statement,
            "user_answer": user_answer,
            "correct_answer": question.correct,
            "is_correct": is_correct
        })

        past_attempts = (
        db.session.query(Score)
        .filter(Score.quiz_id == quiz_id, Score.user_id == current_user.id)
        .order_by(Score.attempted_at.desc())
        .all()
    )
    
    return render_template('quiz_result.html', correct_count=correct_count, score=score, total=total, question_results=question_results,  past_attempts=past_attempts)
