from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'

# SQLite database – file will be created automatically in the project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pass_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def home():
    return "Password Manager is running. Database: SQLite (pass_manager.db)"

# Create the database file and any tables (none yet, but this ensures the file exists)
with app.app_context():
    db.create_all()
    print("Database 'pass_manager.db' ready.")

if __name__ == '__main__':
    app.run(debug=True) 