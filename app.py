from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pass_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  

    # Relationship to stored passwords
    password_entries = db.relationship('PasswordEntry', backref='owner', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class PasswordEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    site_name = db.Column(db.String(100), nullable=False)
    site_url = db.Column(db.String(200))
    encrypted_username = db.Column(db.Text, nullable=False)   # encrypted actual username
    encrypted_password = db.Column(db.Text, nullable=False)   # encrypted actual password
    encrypted_notes = db.Column(db.Text, default='')           # encrypted additional notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PasswordEntry {self.site_name}>"


@app.route('/')
def home():
    return "Password Manager is running. Database: SQLite (pass_manager.db)"

with app.app_context():
    db.create_all()
    print("Database 'pass_manager.db' ready with tables.")

if __name__ == '__main__':
    app.run(debug=True)