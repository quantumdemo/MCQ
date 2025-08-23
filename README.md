# MCQ Test & Exam Management Web Application

This is a full-featured web application for creating, managing, and administering Multiple-Choice Question (MCQ) exams. It provides a complete solution for both administrators/instructors and students.

## Features

### Admin / Instructor Features
- **Secure Authentication:** Admins have a secure login.
- **Question Management:** Full CRUD (Create, Read, Update, Delete) functionality for questions with a rich-text editor (CKEditor 4).
- **Dynamic Options:** Add, remove, and edit multiple-choice options for each question, including marking the correct answer(s).
- **Exam Management:** Full CRUD functionality for creating exams, setting time limits, passing scores, and associating questions from the bank.
- **Bulk Import:** A robust tool to import questions in bulk from a CSV file.
- **Analytics Dashboard:** A dashboard to view high-level statistics about the number of users, questions, and exams.

### Student Features
- **Secure Authentication:** Students can register and log in to their own dashboard.
- **Student Dashboard:** A personalized dashboard showing all available exams.
- **Exam Taking Interface:** A full-featured, single-page interface for taking exams with a countdown timer, question palette, and progress saving via `localStorage`.
- **Automated Grading:** Exam submissions are automatically graded, and the results are saved.
- **Results Review:** Students can view a detailed breakdown of their exam results, showing their answers against the correct ones, along with explanations.
- **Practice Mode:** A non-graded mode where students can generate custom quizzes based on subject or topic to practice.

### Technical Features
- **Role-Based Access Control:** A clear distinction between Admin and Student roles, with protected routes for each.
- **Custom CLI Commands:** A command (`flask create-admin`) is provided to securely create the initial administrator account.
- **Comprehensive Test Suite:** The application is covered by **25 automated tests** using `pytest`, ensuring stability and reliability.
- **Database Migrations:** Uses `Flask-Migrate` to manage database schema changes.

## Tech Stack
- **Backend:** Flask (Python)
- **Database:** SQLAlchemy with SQLite (for development)
- **Frontend:** HTML5, Bootstrap 5, Vanilla JavaScript
- **Forms:** Flask-WTF
- **Testing:** Pytest

---

## Setup & Installation

### 1. Prerequisites
- Python 3.9+
- `pip` package installer

### 2. Clone the Repository
```bash
git clone <repository_url>
cd <repository_directory>
```

### 3. Create a Virtual Environment
It is highly recommended to use a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 4. Install Dependencies
Install all required packages from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
The application uses a `.env` file for configuration, but it is not included in the repository for security. The application will use default values if it's not present. For a production setup, you would create a `.env` file with a `SECRET_KEY`.

### 6. Initialize the Database
Run the database migrations to create the database schema.
```bash
export FLASK_APP=run.py  # On Windows, use `set FLASK_APP=run.py`
flask db upgrade
```

---

## Running the Application

### 1. Create an Admin User
Before you can log in as an admin, you need to create one using the custom CLI command.
```bash
# Usage: flask create-admin <username> <email> <password>
flask create-admin youradmin youradmin@example.com yourpassword
```
This will create a user with the 'Admin' role. You can then log in with these credentials.

### 2. Run the Development Server
```bash
flask run
```
The application will be available at `http://127.0.0.1:5000`.

---

## Running Tests
The project includes a comprehensive test suite. To run the tests, execute the following command from the root directory:
```bash
pytest
```
This will discover and run all 25 tests and report the results.
