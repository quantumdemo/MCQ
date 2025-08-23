from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     SelectField, TextAreaField, FormField, FieldList, IntegerField, SelectMultipleField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class OptionForm(FlaskForm):
    """Sub-form for a single multiple-choice option."""
    option_text = StringField('Option', validators=[DataRequired()])
    is_correct = BooleanField('Correct?')

    class Meta:
        # This is needed to prevent CSRF validation on the sub-form
        csrf = False

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=2, max=100)])
    topic = StringField('Topic', validators=[DataRequired(), Length(min=2, max=100)])
    difficulty = SelectField('Difficulty', choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')],
                             validators=[DataRequired()])
    options = FieldList(FormField(OptionForm), min_entries=2, max_entries=5)
    explanation = TextAreaField('Explanation')
    submit = SubmitField('Save Question')

class ExamForm(FlaskForm):
    title = StringField('Exam Title', validators=[DataRequired(), Length(min=5, max=150)])
    time_limit = IntegerField('Time Limit (minutes)', validators=[DataRequired()])
    passing_score = IntegerField('Passing Score (%)', default=70, validators=[DataRequired()])
    negative_marking = BooleanField('Enable Negative Marking', default=False)
    randomize_questions = BooleanField('Randomize Question Order', default=True)
    questions = SelectMultipleField('Select Questions', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Exam')

class FileUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired(), FileAllowed(['csv'], 'CSV files only!')])
    submit = SubmitField('Upload')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
