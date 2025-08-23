from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt, mail
from app.models import User
from app.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from flask_mail import Message

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/index")
def index():
    return render_template('index.html', title='Home') # I will create this template

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.index'))


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('main.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@main.route("/reset_password", methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('main.login'))
    return render_template('request_reset.html', title='Reset Password', form=form)


@main.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.request_reset'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password_hash = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_password.html', title='Reset Password', form=form)


from app.models import Exam

@main.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == 'Admin':
        return redirect(url_for('admin.dashboard'))

    # For Student
    exams = Exam.query.all()
    practice_mode_setting = Setting.query.filter_by(key='practice_mode_enabled').first()
    is_practice_enabled = practice_mode_setting and practice_mode_setting.value == 'true'

    return render_template('student_dashboard.html', title='Your Dashboard', exams=exams, is_practice_enabled=is_practice_enabled)

from app.models import Setting

@main.route("/practice")
@login_required
def practice_dashboard():
    practice_mode_setting = Setting.query.filter_by(key='practice_mode_enabled').first()
    if not practice_mode_setting or practice_mode_setting.value == 'false':
        flash('Practice mode is currently disabled by the administrator.', 'info')
        return redirect(url_for('main.dashboard'))

    from app.models import Question
    subjects = db.session.query(Question.subject).distinct().all()
    topics = db.session.query(Question.topic).distinct().all()

    subjects = [s[0] for s in subjects]
    topics = [t[0] for t in topics]
    question_count = Question.query.count()

    return render_template('practice_dashboard.html', title='Practice Mode', subjects=subjects, topics=topics, question_count=question_count)

@main.route("/practice/start")
@login_required
def start_practice():
    from app.models import Question
    from sqlalchemy.sql.expression import func
    import json

    subject = request.args.get('subject', 'all')
    topic = request.args.get('topic', 'all')
    num_questions = request.args.get('num_questions', 10, type=int)

    query = Question.query
    if subject != 'all':
        query = query.filter(Question.subject == subject)
    if topic != 'all':
        query = query.filter(Question.topic == topic)

    questions = query.order_by(func.random()).limit(num_questions).all()

    if not questions:
        flash('No questions found matching your criteria. Try a different filter.', 'warning')
        return redirect(url_for('main.practice_dashboard'))

    # Create a mock exam object for the template
    practice_exam = {'id': 0, 'title': 'Practice Quiz', 'time_limit': 0}

    questions_data = []
    for q in questions:
        options = [{'id': opt.id, 'text': opt.option_text, 'is_correct': opt.is_correct} for opt in q.options]
        # Include explanation for practice mode
        questions_data.append({'id': q.id, 'text': q.question_text, 'options': options, 'explanation': q.explanation})

    return render_template('exam_take.html',
                           # exam=practice_exam,
                           exam_json=json.dumps(practice_exam),
                           questions_json=json.dumps(questions_data),
                           is_practice_mode=True)
