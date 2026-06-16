# Secure Password Manager

A secure password manager built with **Python (Flask)** and **SQLite**.  
All sensitive data is encrypted using **Fernet (symmetric encryption)**.  
User login passwords are hashed with salt and stored securely.
**#special features**
- User registration & login
- Add, view, edit, delete stored credentials
- Passwords, usernames, and notes encrypted before storage
- Built‑in password generator
- CSRF protection, XSS prevention, SQL injection safe (ORM)
- One‑click setup & launch

## How to Run (Windows)

1. **Clone or download** this repository.
2. **Double‑click `setup.bat`**.
   - Creates a virtual environment, installs dependencies, and starts the app.
3. Open your browser → **`http://127.0.0.1:5000`**.

> Requires **Python 3.8+** installed and in PATH.

## How to Run (macOS / Linux)

1. Open a terminal in the project folder.
2. Run:  
   ```bash
   chmod +x setup.sh
   ./setup.sh
