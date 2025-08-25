from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Association table for the many-to-many relationship between Exam and Question
exam_questions = db.Table('exam_questions',
    db.Column('exam_id', db.Integer, db.ForeignKey('exam.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True)
)

from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Student') # Roles: Admin, Student
    results = db.relationship('Result', backref='student', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default='Medium') # Easy, Medium, Hard
    explanation = db.Column(db.Text, nullable=True)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Question('{self.question_text[:30]}...', '{self.subject}')"

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    def __repr__(self):
        return f"Option('{self.option_text}', Correct: {self.is_correct})"

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False) # in minutes
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    passing_score = db.Column(db.Integer, default=70)
    negative_marking = db.Column(db.Boolean, default=False)
    randomize_questions = db.Column(db.Boolean, default=True)
    questions = db.relationship('Question', secondary=exam_questions, lazy='joined',
                                backref=db.backref('exams', lazy=True))
    results = db.relationship('Result', backref='exam', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Exam('{self.title}', Time: {self.time_limit} mins)"

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_answers = db.relationship('StudentAnswer', backref='result', lazy=True, cascade="all, delete-orphan")
    score = db.Column(db.Float, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True) # Should only be set upon submission
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)

    def __repr__(self):
        return f"Result(User: {self.user_id}, Exam: {self.exam_id}, Score: {self.score})"

class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)

    question = db.relationship('Question')
    selected_option = db.relationship('Option')

    def __repr__(self):
        return f"StudentAnswer(Result: {self.result_id}, Q: {self.question_id}, A: {self.selected_option_id})"

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"Setting('{self.key}', '{self.value}')"
