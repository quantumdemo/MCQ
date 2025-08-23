from flask import Blueprint, render_template, flash, redirect, url_for, request, Response
from flask_login import login_required
from app.decorators import admin_required
from app.models import Question, Result
from app.forms import QuestionForm
from app import db

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    question_count = Question.query.count()
    exam_count = Exam.query.count()

    stats = {
        'user_count': user_count,
        'question_count': question_count,
        'exam_count': exam_count
    }

    practice_mode_setting = Setting.query.filter_by(key='practice_mode_enabled').first()
    if not practice_mode_setting:
        practice_mode_setting = Setting(key='practice_mode_enabled', value='true')
        db.session.add(practice_mode_setting)
        db.session.commit()

    is_practice_enabled = practice_mode_setting.value == 'true'

    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats, is_practice_enabled=is_practice_enabled)

@admin.route('/settings/toggle_practice', methods=['POST'])
@login_required
@admin_required
def toggle_practice_mode():
    setting = Setting.query.filter_by(key='practice_mode_enabled').first()
    if setting:
        if setting.value == 'true':
            setting.value = 'false'
            flash('Practice Mode has been locked for all students.', 'warning')
        else:
            setting.value = 'true'
            flash('Practice Mode has been unlocked for all students.', 'success')
        db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin.route('/analytics')
@login_required
@admin_required
def analytics():
    from sqlalchemy import func
    from app.models import Result, User
    from sqlalchemy.orm import joinedload

    exam_stats = db.session.query(
        Exam.id,
        Exam.title,
        func.count(Result.id).label('attempts'),
        func.avg(Result.score).label('avg_score'),
        func.max(Result.score).label('max_score'),
        func.min(Result.score).label('min_score')
    ).join(Result, Result.exam_id == Exam.id).group_by(Exam.id, Exam.title).all()

    # New query for detailed results
    all_results = Result.query.options(
        joinedload(Result.student),
        joinedload(Result.exam)
    ).order_by(Result.submitted_at.desc()).all()

    return render_template('admin/analytics.html', title='Exam Analytics', exam_stats=exam_stats, all_results=all_results)

@admin.route('/questions')
@login_required
@admin_required
def list_questions():
    selected_subject = request.args.get('subject', 'all')
    selected_topic = request.args.get('topic', 'all')

    query = Question.query
    if selected_subject != 'all':
        query = query.filter(Question.subject == selected_subject)
    if selected_topic != 'all':
        query = query.filter(Question.topic == selected_topic)

    questions = query.all()

    subjects = [s[0] for s in db.session.query(Question.subject).distinct().all()]
    topics = [t[0] for t in db.session.query(Question.topic).distinct().all()]

    return render_template('admin/questions.html',
                           title='Question Bank',
                           questions=questions,
                           subjects=subjects,
                           topics=topics,
                           selected_subject=selected_subject,
                           selected_topic=selected_topic)

from app.models import Option, Exam, User, Question, Setting
from app.forms import ExamForm, FileUploadForm

@admin.route('/question/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            question_text=form.question_text.data,
            subject=form.subject.data,
            topic=form.topic.data,
            difficulty=form.difficulty.data,
            explanation=form.explanation.data
        )
        db.session.add(question)
        # Create and associate options
        for option_data in form.options.data:
            option = Option(
                option_text=option_data['option_text'],
                is_correct=option_data['is_correct'],
                question=question
            )
            db.session.add(option)
        db.session.commit()
        flash('The question has been created!', 'success')
        return redirect(url_for('admin.list_questions'))
    return render_template('admin/create_question.html', title='New Question', form=form, legend='New Question')

@admin.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=question) # Pass the object to pre-populate simple fields
    if form.validate_on_submit():
        question.question_text = form.question_text.data
        question.subject = form.subject.data
        question.topic = form.topic.data
        question.difficulty = form.difficulty.data
        question.explanation = form.explanation.data

        # Delete old options and create new ones
        Option.query.filter_by(question_id=question.id).delete()
        for option_data in form.options.data:
            option = Option(
                option_text=option_data['option_text'],
                is_correct=option_data['is_correct'],
                question_id=question.id
            )
            db.session.add(option)

        db.session.commit()
        flash('The question has been updated!', 'success')
        return redirect(url_for('admin.list_questions'))

    elif request.method == 'GET':
        # Manually populate the FieldList
        while len(form.options) > 0:
            form.options.pop_entry()
        for option in question.options:
            form.options.append_entry(option)

    return render_template('admin/create_question.html', title='Edit Question', form=form, legend=f'Edit Question (ID: {question.id})')

@admin.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)

    # Manually clear the many-to-many relationship with exams
    question.exams.clear()

    db.session.delete(question)
    db.session.commit()
    flash('The question and its associations have been deleted!', 'success')
    return redirect(url_for('admin.list_questions'))

# Exam Management Routes
# ========================

@admin.route('/exams')
@login_required
@admin_required
def list_exams():
    exams = Exam.query.all()
    return render_template('admin/exams.html', title='Manage Exams', exams=exams)

@admin.route('/exam/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_exam():
    form = ExamForm()

    # Filtering logic
    selected_subject = request.args.get('subject', 'all')
    selected_topic = request.args.get('topic', 'all')

    questions_query = Question.query
    if selected_subject != 'all':
        questions_query = questions_query.filter(Question.subject == selected_subject)
    if selected_topic != 'all':
        questions_query = questions_query.filter(Question.topic == selected_topic)

    filtered_questions = questions_query.all()
    form.questions.choices = [(q.id, f"{q.id}: {q.question_text[:50]}...") for q in filtered_questions]

    # Populate filter dropdowns
    subjects = ['all'] + [s[0] for s in db.session.query(Question.subject).distinct().all()]
    topics = ['all'] + [t[0] for t in db.session.query(Question.topic).distinct().all()]

    if form.validate_on_submit():
        exam = Exam(
            title=form.title.data,
            time_limit=form.time_limit.data,
            passing_score=form.passing_score.data,
            negative_marking=form.negative_marking.data,
            randomize_questions=form.randomize_questions.data
        )
        # Add selected questions to the exam
        for question_id in form.questions.data:
            question = Question.query.get(question_id)
            if question:
                exam.questions.append(question)

        db.session.add(exam)
        db.session.commit()
        flash('The exam has been created!', 'success')
        return redirect(url_for('admin.list_exams'))

    return render_template('admin/create_exam.html', title='New Exam', form=form, legend='Create New Exam',
                           subjects=subjects, topics=topics,
                           selected_subject=selected_subject, selected_topic=selected_topic)

@admin.route('/exam/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    form = ExamForm(obj=exam)

    # Filtering logic
    selected_subject = request.args.get('subject', 'all')
    selected_topic = request.args.get('topic', 'all')

    questions_query = Question.query
    if selected_subject != 'all':
        questions_query = questions_query.filter(Question.subject == selected_subject)
    if selected_topic != 'all':
        questions_query = questions_query.filter(Question.topic == selected_topic)

    filtered_questions = questions_query.all()
    form.questions.choices = [(q.id, f"{q.id}: {q.question_text[:50]}...") for q in filtered_questions]

    # Populate filter dropdowns
    subjects = ['all'] + [s[0] for s in db.session.query(Question.subject).distinct().all()]
    topics = ['all'] + [t[0] for t in db.session.query(Question.topic).distinct().all()]

    if form.validate_on_submit():
        exam.title = form.title.data
        exam.time_limit = form.time_limit.data
        exam.passing_score = form.passing_score.data
        exam.negative_marking = form.negative_marking.data
        exam.randomize_questions = form.randomize_questions.data

        # Update questions
        exam.questions.clear()
        for question_id in form.questions.data:
            question = Question.query.get(question_id)
            if question:
                exam.questions.append(question)

        db.session.commit()
        flash('The exam has been updated!', 'success')
        return redirect(url_for('admin.list_exams'))

    elif request.method == 'GET':
        # Pre-select the questions that are already associated with the exam
        form.questions.data = [q.id for q in exam.questions]

    return render_template('admin/create_exam.html', title='Edit Exam', form=form, legend=f'Edit Exam (ID: {exam.id})',
                           subjects=subjects, topics=topics,
                           selected_subject=selected_subject, selected_topic=selected_topic)

@admin.route('/exam/<int:exam_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash('The exam has been deleted!', 'success')
    return redirect(url_for('admin.list_exams'))

# Bulk Import Route
# ===================

import csv
import io

import csv
import io

@admin.route('/questions/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_questions():
    form = FileUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        stream = io.TextIOWrapper(file, encoding='utf-8')
        reader = csv.DictReader(stream)

        new_questions = []
        error_rows = []

        for row_num, row in enumerate(reader, 2): # Start from row 2 for error reporting
            try:
                if not all(k in row and row[k] for k in ['question_text', 'subject', 'topic', 'difficulty']):
                    error_rows.append(row_num)
                    continue

                question = Question(
                    question_text=row['question_text'],
                    subject=row['subject'],
                    topic=row['topic'],
                    difficulty=row['difficulty'],
                    explanation=row.get('explanation', '')
                )

                options = []
                for i in range(1, 6):
                    option_text_key = f'option{i}_text'
                    if row.get(option_text_key):
                        is_correct_key = f'option{i}_is_correct'
                        is_correct = row.get(is_correct_key, '').lower() in ['1', 'true', 'yes']
                        options.append(Option(option_text=row[option_text_key], is_correct=is_correct))

                if len(options) < 2:
                    error_rows.append(row_num)
                    continue

                question.options = options
                new_questions.append(question)

            except Exception:
                error_rows.append(row_num)

        if new_questions:
            db.session.add_all(new_questions)
            db.session.commit()

        success_count = len(new_questions)
        error_count = len(error_rows)

        flash(f'Import complete. Successfully added {success_count} questions. Skipped {error_count} rows due to errors.', 'success')
        return redirect(url_for('admin.list_questions'))

    return render_template('admin/import_questions.html', title='Bulk Import Questions', form=form)


@admin.route('/students')
@login_required
@admin_required
def list_students():
    students = User.query.filter_by(role='Student').all()
    return render_template('admin/students.html', title='Manage Students', students=students)

@admin.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'Student':
        flash('This user is not a student.', 'danger')
        return redirect(url_for('admin.list_students'))
    db.session.delete(student)
    db.session.commit()
    flash('The student has been deleted!', 'success')
    return redirect(url_for('admin.list_students'))

# Export Routes
# ===================

@admin.route('/exam/<int:exam_id>/export/csv')
@login_required
@admin_required
def export_exam_results_csv(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    results = Result.query.filter_by(exam_id=exam_id).options(db.joinedload(Result.student)).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['Student ID', 'Student Username', 'Score', 'Submitted At'])

    # Rows
    for result in results:
        writer.writerow([
            result.student.id,
            result.student.username,
            f"{result.score}%",
            result.submitted_at.strftime('%Y-%m-%d %H:%M') if result.submitted_at else 'N/A'
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=exam_{exam_id}_all_results.csv"}
    )

@admin.route('/result/<int:result_id>/export/csv')
@login_required
@admin_required
def export_result_csv(result_id):
    result = Result.query.options(
        db.joinedload(Result.student),
        db.joinedload(Result.exam).joinedload(Exam.questions).joinedload(Question.options)
    ).get_or_404(result_id)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['Exam Title', 'Student', 'Score', 'Date Taken'])
    writer.writerow([result.exam.title, result.student.username, f"{result.score}%", result.submitted_at.strftime('%Y-%m-%d %H:%M')])
    writer.writerow([]) # Spacer
    writer.writerow(['Question', 'Your Answer', 'Correct Answer', 'Result'])

    student_answers_map = {sa.question_id: sa.selected_option_id for sa in result.student_answers}

    for question in result.exam.questions:
        selected_option_id = student_answers_map.get(question.id)
        selected_option_text = ''
        correct_option_text = ''
        is_correct = False

        for option in question.options:
            if option.is_correct:
                correct_option_text = option.option_text
            if option.id == selected_option_id:
                selected_option_text = option.option_text

        if selected_option_id and selected_option_text == correct_option_text:
            is_correct = True

        writer.writerow([
            question.question_text,
            selected_option_text,
            correct_option_text,
            'Correct' if is_correct else 'Incorrect'
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=result_{result_id}.csv"}
    )

from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Exam Result', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_table(self, header, data):
        self.set_font('Arial', 'B', 10)
        col_widths = [70, 40, 40, 30]
        for i, h in enumerate(header):
            self.cell(col_widths[i], 10, h, 1)
        self.ln()

        self.set_font('Arial', '', 10)
        for row in data:
            for i, item in enumerate(row):
                self.cell(col_widths[i], 10, str(item), 1)
            self.ln()

@admin.route('/result/<int:result_id>/export/pdf')
@login_required
@admin_required
def export_result_pdf(result_id):
    result = Result.query.options(
        db.joinedload(Result.student),
        db.joinedload(Result.exam).joinedload(Exam.questions).joinedload(Question.options)
    ).get_or_404(result_id)

    pdf = PDF()
    pdf.add_page()

    # Summary
    pdf.chapter_title('Summary')
    summary_text = (
        f"Exam: {result.exam.title}\n"
        f"Student: {result.student.username}\n"
        f"Score: {result.score}%\n"
        f"Date: {result.submitted_at.strftime('%Y-%m-%d %H:%M')}"
    )
    pdf.chapter_body(summary_text)

    # Detailed Results
    pdf.chapter_title('Detailed Results')
    table_header = ['Question', 'Your Answer', 'Correct Answer', 'Result']
    table_data = []

    student_answers_map = {sa.question_id: sa.selected_option_id for sa in result.student_answers}

    for question in result.exam.questions:
        selected_option_id = student_answers_map.get(question.id)
        selected_option_text = ''
        correct_option_text = ''
        is_correct = False

        for option in question.options:
            if option.is_correct:
                correct_option_text = option.option_text
            if option.id == selected_option_id:
                selected_option_text = option.option_text

        if selected_option_id and selected_option_text == correct_option_text:
            is_correct = True

        table_data.append([
            question.question_text,
            selected_option_text,
            correct_option_text,
            'Correct' if is_correct else 'Incorrect'
        ])

    pdf.add_table(table_header, table_data)

    return Response(
        bytes(pdf.output()),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment;filename=result_{result_id}.pdf'}
    )
