import click
from flask.cli import with_appcontext
from app import db, bcrypt
from app.models import User

def register_commands(app):
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    def create_admin(username, email, password):
        """Creates a new admin user."""
        if User.query.filter_by(email=email).first():
            click.echo('Error: Email already exists.')
            return
        if User.query.filter_by(username=username).first():
            click.echo('Error: Username already exists.')
            return

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role='Admin'
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Admin user "{username}" created successfully.')
