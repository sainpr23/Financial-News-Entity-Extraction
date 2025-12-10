from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

from ner_engine import perform_ner

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # replace with a secure value for real deployments


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def index():
    """Render the main page with an empty input, like a fresh screen."""
    return render_template(
        "index.html",
        input_text="",
        results=None,
        error=None,
        user=session.get("user"),
        require_login=False,
    )


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))

        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash),
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            flash("Username or email already exists.", "error")
            return redirect(url_for("signup"))

        session["user"] = username
        session.pop("attempts", None)
        return redirect(url_for("index"))

    return render_template("signup.html", user=session.get("user"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if row and check_password_hash(row["password_hash"], password):
            session["user"] = row["username"]
            session.pop("attempts", None)
            return redirect(url_for("index"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("login"))

    return render_template("login.html", user=session.get("user"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/settings")
def settings():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("settings.html", user=user)


@app.route("/extract", methods=["POST"])
def extract():
    """Handle form submission, run NER, and display extracted entities."""
    text = request.form.get("text", "").strip()

    # Track anonymous usage attempts in the session.
    user = session.get("user")
    attempts = session.get("attempts", 0)

    require_login = False

    if not user:
        if attempts >= 3:
            require_login = True
        else:
            session["attempts"] = attempts + 1

    error = None
    results = None

    if require_login:
        error = "You have reached the limit for anonymous use. Please sign up or log in to continue."
    elif not text:
        error = "Please enter some financial news text before submitting."
    elif len(text) > 10000:
        error = "Input text is too long. Please provide a shorter sample (max 10,000 characters)."
    else:
        # Call the NER engine to extract entities
        results = perform_ner(text)

    return render_template(
        "index.html",
        input_text="" if require_login else text,
        results=None if require_login else results,
        error=error,
        user=user,
        require_login=require_login,
    )


if __name__ == "__main__":
    init_db()
    # For a college project, enabling debug=True is convenient during development.
    # In production, you would set debug=False.
    app.run(debug=True)
