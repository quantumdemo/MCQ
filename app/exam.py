from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.models import Exam, Result, StudentAnswer
from app import db

exam_bp = Blueprint('exam', __name__, url_prefix='/exam')

@exam_bp.route('/<int:exam_id>/start', methods=['POST'])
@login_required
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    # Check if the user has already started or finished this exam
    existing_result = Result.query.filter_by(user_id=current_user.id, exam_id=exam.id).first()
    if existing_result:
        flash('You have already attempted this exam.', 'info')
        # In the future, this might redirect to the results page or the exam page if it's resumable.
        return redirect(url_for('main.dashboard'))

    # Create a new result entry to mark the start of the attempt
    new_result = Result(
        user_id=current_user.id,
        exam_id=exam.id,
        score=0 # Placeholder score
    )
    db.session.add(new_result)
    db.session.commit()

    return redirect(url_for('exam.take_exam', exam_id=exam.id))

@exam_bp.route('/<int:exam_id>/take')
@login_required
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    # Ensure user has started the exam and doesn't already have a final score
    result = Result.query.filter_by(user_id=current_user.id, exam_id=exam.id).first_or_404()

    # Convert to list to make it mutable for shuffling
    questions = list(exam.questions)

    if not questions:
        flash('This exam has no questions. Please contact an administrator.', 'warning')
        return redirect(url_for('main.dashboard'))

    # Randomize questions if the exam setting is enabled
    if exam.randomize_questions:
        import random
        random.shuffle(questions)

    # Pass questions to the template. We can serialize them to JSON for easier JS access.
    import json
    questions_data = []
    for q in questions:
        # Include is_correct for practice mode functionality
        options = [{'id': opt.id, 'text': opt.option_text, 'is_correct': opt.is_correct} for opt in q.options]
        # Include explanation for practice mode
        questions_data.append({'id': q.id, 'text': q.question_text, 'options': options, 'explanation': q.explanation})

    # Fetch practice mode setting to pass to the template
    from app.models import Setting
    practice_mode_setting = Setting.query.filter_by(key='practice_mode_enabled').first()
    is_practice_mode = practice_mode_setting and practice_mode_setting.value == 'true'

    exam_data = {
        'id': exam.id,
        'title': exam.title,
        'time_limit': exam.time_limit
    }

    return render_template('exam_take.html',
                           # title=f"Taking: {exam.title}",
                           # exam=exam,
                           exam_json=json.dumps(exam_data),
                           questions_json=json.dumps(questions_data),
                           is_practice_mode=is_practice_mode)

@exam_bp.route('/<int:exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    result = Result.query.filter_by(user_id=current_user.id, exam_id=exam.id).first_or_404()

    # Prevent re-submission if already scored
    if result.submitted_at:
        return jsonify({'error': 'Exam already submitted.'}), 400

    answers = request.get_json()
    if not answers:
        return jsonify({'error': 'No answers provided.'}), 400

    correct_answers = 0
    total_questions = len(exam.questions)

    for question in exam.questions:
        correct_option_id = None
        for option in question.options:
            if option.is_correct:
                correct_option_id = option.id
                break

        user_answer_id = answers.get(str(question.id))
        if user_answer_id and int(user_answer_id) == correct_option_id:
            correct_answers += 1

    # Calculate score
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    # Save the student's answers
    for q_id, opt_id in answers.items():
        student_answer = StudentAnswer(
            result_id=result.id,
            question_id=int(q_id),
            selected_option_id=int(opt_id)
        )
        db.session.add(student_answer)

    # Update result record
    result.score = round(score, 2)
    result.submitted_at = db.func.now()
    db.session.commit()

    results_url = url_for('exam.view_result', result_id=result.id)
    return jsonify({'message': 'Exam submitted successfully!', 'redirect_url': results_url})

@exam_bp.route('/result/<int:result_id>/view')
@login_required
def view_result(result_id):
    result = Result.query.get_or_404(result_id)

    # Security check: only the user who took the exam can see the result
    if result.user_id != current_user.id:
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('main.dashboard'))

    # To display the results, we need to reconstruct what the student answered for each question.
    # A dictionary mapping question_id to the student's selected_option_id is useful.
    student_answers_map = {sa.question_id: sa.selected_option_id for sa in result.student_answers}

    return render_template('results_view.html',
                           title=f"Results for {result.exam.title}",
                           result=result,
                           student_answers_map=student_answers_map)
