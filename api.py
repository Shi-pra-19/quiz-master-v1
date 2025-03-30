from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from model import db, Subject, Chapter, Quiz
from datetime import datetime

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

class SubjectResource(Resource):
    def get(self, subject_id=None):
        if subject_id:
            subject = Subject.query.get(subject_id)
            return jsonify(subject={"id": subject.id, "name": subject.name, "description": subject.description}) if subject else ({"error": "Not found"}, 404)
        subjects = Subject.query.all()
        return jsonify(subjects=[{"id": s.id, "name": s.name, "description": s.description} for s in subjects])

    def post(self):
        data = request.json
        subject = Subject(name=data['name'], description=data.get('description', ''))
        db.session.add(subject)
        db.session.commit()
        return jsonify({"message": "Subject created", "id": subject.id})

    def put(self, subject_id):
        subject = Subject.query.get(subject_id)
        if not subject:
            return {"error": "Not found"}, 404
        data = request.json
        subject.name = data.get('name', subject.name)
        subject.description = data.get('description', subject.description)
        db.session.commit()
        return jsonify({"message": "Subject updated"})

    def delete(self, subject_id):
        subject = Subject.query.get(subject_id)
        if not subject:
            return {"error": "Not found"}, 404
        db.session.delete(subject)
        db.session.commit()
        return jsonify({"message": "Subject deleted"})

class ChapterResource(Resource):
    def get(self, chapter_id=None):
        if chapter_id:
            chapter = Chapter.query.get(chapter_id)
            return jsonify(chapter={"id": chapter.id, "name": chapter.name, "subject_id": chapter.subject_id}) if chapter else ({"error": "Not found"}, 404)
        chapters = Chapter.query.all()
        return jsonify(chapters=[{"id": c.id, "name": c.name, "subject_id": c.subject_id} for c in chapters])

    def post(self):
        data = request.json
        chapter = Chapter(name=data['name'], description=data['description'], subject_id=data['subject_id'])
        db.session.add(chapter)
        db.session.commit()
        return jsonify({"message": "Chapter created", "id": chapter.id})

    def put(self, chapter_id):
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return {"error": "Not found"}, 404
        data = request.json
        chapter.name = data.get('name', chapter.name)
        chapter.description = data.get('description', chapter.description)
        db.session.commit()
        return jsonify({"message": "Chapter updated"})

    def delete(self, chapter_id):
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return {"error": "Not found"}, 404
        db.session.delete(chapter)
        db.session.commit()
        return jsonify({"message": "Chapter deleted"})

class QuizResource(Resource):
    def get(self, quiz_id=None):
        if quiz_id:
            quiz = Quiz.query.get(quiz_id)
            return jsonify(quiz={"id": quiz.id, "chapter_id": quiz.chapter_id, "date": quiz.date.strftime("%Y-%m-%d"), "duration": quiz.duration}) if quiz else ({"error": "Not found"}, 404)
        quizzes = Quiz.query.all()
        return jsonify(quizzes=[{"id": q.id, "chapter_id": q.chapter_id, "date": q.date.strftime("%Y-%m-%d"), "duration": q.duration} for q in quizzes])

    def post(self):
        data = request.json
        quiz = Quiz(chapter_id=data['chapter_id'], date=datetime.strptime(data['date'], "%Y-%m-%d").date(), duration=data['duration'])
        db.session.add(quiz)
        db.session.commit()
        return jsonify({"message": "Quiz created", "id": quiz.id})

    def put(self, quiz_id):
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return {"error": "Not found"}, 404
        data = request.json
        quiz.date = datetime.strptime(data.get('date', quiz.date.strftime("%Y-%m-%d")), "%Y-%m-%d").date()
        quiz.duration = data.get('duration', quiz.duration)
        db.session.commit()
        return jsonify({"message": "Quiz updated"})

    def delete(self, quiz_id):
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return {"error": "Not found"}, 404
        db.session.delete(quiz)
        db.session.commit()
        return jsonify({"message": "Quiz deleted"})

class UserResource(Resource):
    def get(self, id=None):
        if id:
            return jsonify(user={"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}) if user else ({"message": "User not found"}, 404)
        return jsonify(users=[{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role} for u in users])
    def post(self):
        data = request.json
        new_user = User(full_name=data["full_name"], email=data["email"], role=data.get("role", "user"))
        new_user.set_password(data["password"])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created", "id": new_user.id})

    def put(self, id):
        user = User.query.get(id)
        if not user:
            return jsonify({"message": "User not found"}), 404
        data = request.json
        user.full_name = data.get("full_name", user.full_name)
        user.email = data.get("email", user.email)
        user.role = data.get("role", user.role)
        if "password" in data:
            user.set_password(data["password"])
        db.session.commit()
        return jsonify({"message": "User updated"})

    def delete(self, id):
        user = User.query.get(id)
        if not user:
            return jsonify({"message": "User not found"}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted"})


api.add_resource(SubjectResource, "/subjects", "/subjects/<int:subject_id>")
api.add_resource(ChapterResource, "/chapters", "/chapters/<int:chapter_id>")
api.add_resource(QuizResource, "/quizzes", "/quizzes/<int:quiz_id>")
api.add_resource(UserResource, "/users", "/users/<int:id>")

