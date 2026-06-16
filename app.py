from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from cryptography.fernet import Fernet
import os
from flask_wtf.csrf import CSRFProtect
app = Flask(__name__)
SECRET_KEY_FILE = 'secret_key.txt'

def load_or_generate_secret_key():
    if not os.path.exists(SECRET_KEY_FILE):
        # Generate a new random secret key
        secret = os.urandom(24)
        with open(SECRET_KEY_FILE, 'wb') as f:
            f.write(secret)
        print("New secret key generated.")
    with open(SECRET_KEY_FILE, 'rb') as f:
        return f.read()

app.config['SECRET_KEY'] = load_or_generate_secret_key()
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pass_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
KEY_FILE = 'secret.key'

    
def load_or_generate_key():
    if not os.path.exists(KEY_FILE):
        new_key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(new_key)
        print("New encryption key generated and saved.")
    with open(KEY_FILE, 'rb') as key_file:
        key = key_file.read()
    return key

encryption_key = load_or_generate_key()
cipher = Fernet(encryption_key)
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

class PasswordEntryForm(FlaskForm):
    site_name = StringField('Site Name', validators=[DataRequired()])
    site_url = StringField('Site URL', validators=[Optional()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save')
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/')
def home(): 
    return render_template('home.html') 
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
    user_id = session.get('user_id')
    entries = PasswordEntry.query.filter_by(user_id=user_id).order_by(PasswordEntry.created_at.desc()).all()
    return render_template('dashboard.html', username=session.get('username'), entries=entries)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_entry():
    form = PasswordEntryForm()
    if form.validate_on_submit():
        user_id = session['user_id']
        # Encrypt the sensitive fields
        enc_username = encrypt_data(form.username.data)
        enc_password = encrypt_data(form.password.data)
        enc_notes = encrypt_data(form.notes.data) if form.notes.data else encrypt_data('')

        new_entry = PasswordEntry(
            user_id=user_id,
            site_name=form.site_name.data,
            site_url=form.site_url.data,
            encrypted_username=enc_username,
            encrypted_password=enc_password,
            encrypted_notes=enc_notes
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Password entry added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_entry.html', form=form)

@app.route('/view/<int:entry_id>')
@login_required
def view_entry(entry_id):
    entry = PasswordEntry.query.get_or_404(entry_id)
    # Security check: only the owner can view
    if entry.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    plain_username = decrypt_data(entry.encrypted_username)
    plain_password = decrypt_data(entry.encrypted_password)
    plain_notes = decrypt_data(entry.encrypted_notes) if entry.encrypted_notes else ''
    return render_template('view_entry.html', entry=entry,
                           plain_username=plain_username,
                           plain_password=plain_password,
                           plain_notes=plain_notes)

@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = PasswordEntry.query.get_or_404(entry_id)
    if entry.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    form = PasswordEntryForm()
    if form.validate_on_submit():
        entry.site_name = form.site_name.data
        entry.site_url = form.site_url.data
        entry.encrypted_username = encrypt_data(form.username.data)
        entry.encrypted_password = encrypt_data(form.password.data)
        entry.encrypted_notes = encrypt_data(form.notes.data) if form.notes.data else encrypt_data('')
        db.session.commit()
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        form.site_name.data = entry.site_name
        form.site_url.data = entry.site_url
        form.username.data = decrypt_data(entry.encrypted_username)
        form.password.data = decrypt_data(entry.encrypted_password)
        form.notes.data = decrypt_data(entry.encrypted_notes) if entry.encrypted_notes else ''
    return render_template('edit_entry.html', form=form, entry=entry)

@app.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = PasswordEntry.query.get_or_404(entry_id)
    if entry.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted.', 'info')
    return redirect(url_for('dashboard'))
with app.app_context():
    db.create_all()
    print("Database ready.")

if __name__ == '__main__':
    app.run(debug=True)