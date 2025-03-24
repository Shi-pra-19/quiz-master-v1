from flask_login import login_user, login_required, current_user, logout_user
from flask import Flask, redirect, url_for, render_template, request, flash,session, Blueprint
from model import Subject, Quiz, Score, Chapter, Question
from datetime import date, datetime, timedelta
from extensions import db
from collections import defaultdict
from sqlalchemy.sql import func

user = Blueprint("user", __name__)

@user.route('/home')
@login_required
def home():
    today = date.today()
    quizzes = Quiz.query.filter(Quiz.date >= today).order_by(Quiz.date).all()
    past_quizzes = Quiz.query.filter(Quiz.date < today).order_by(Quiz.date.desc()).all()
    return render_template('user_home.html', quizzes=quizzes, past_quizzes=past_quizzes)


@user.route('/subject')
@login_required
def subject():
    subjects = Subject.query.all()
    return render_template('user_subject.html', subjects = subjects)

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


@user.route('/start_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        score = 0
        total = len(quiz.questions)
        user_answers = {} 
        
        for question in quiz.questions:
            selected_answer = request.form.get(str(question.id))
            user_answers[str(question.id)] = selected_answer 
            
            if selected_answer == question.correct:
                score += 1
        percentage = (score / total) * 100 if total > 0 else 0

        new_score = Score(
            user_id=current_user.id,
            quiz_id=quiz.id,
            score=percentage,
            attempted_at=datetime.utcnow() 
        )
        db.session.add(new_score)
        db.session.commit()

      
        session['quiz_results'] = {
            'score': score,
            'total': total,
            'user_answers': user_answers
        }

        
        return redirect(url_for('user.quiz_result', quiz_id=quiz_id))

    return render_template('start_quiz.html', quiz=quiz)

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
