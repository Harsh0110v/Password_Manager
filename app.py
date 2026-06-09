from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm          # <-- correct
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from cryptography.fernet import Fernet
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pass_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

KEY_FILE = 'secret.key'

def load_or_generate_key():
    if not os.path.exists(KEY_FILE):
        # Generate a new key and write it to the file
        new_key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(new_key)
        print("New encryption key generated and saved.")

    # Read the key from the file
    with open(KEY_FILE, 'rb') as key_file:
        key = key_file.read()
    return key
    
encryption_key = load_or_generate_key()
cipher= Fernet(encryption_key)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  

    password_entries = db.relationship('PasswordEntry', backref='owner', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

class PasswordEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    site_name = db.Column(db.String(100), nullable=False)
    site_url = db.Column(db.String(200))
    encrypted_username = db.Column(db.Text, nullable=False)   
    encrypted_password = db.Column(db.Text, nullable=False)   
    encrypted_notes = db.Column(db.Text, default='')          
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PasswordEntry {self.site_name}>"
    
def encrypt_data(plain_text):
    return cipher.encrypt(plain_text.encode()).decode()

def decrypt_data(encrypted_text):
    return cipher.decrypt(encrypted_text.encode()).decode()

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('base.html')

    
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already taken. Choose a different one.', 'danger')
            return render_template('register.html', form=form)
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

with app.app_context():
    db.create_all()
    print("Database ready.")

if __name__ == '__main__':
    app.run(debug=True)