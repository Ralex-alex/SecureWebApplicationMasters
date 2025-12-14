from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return "App is running."

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, "user")
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return """
        <h2>Register</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password"><br>
            <button type="submit">Register</button>
        </form>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect("/dashboard")

        return "Invalid credentials"

    return """
        <h2>Login</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password"><br>
            <button type="submit">Login</button>
        </form>
    """


@app.route("/dashboard")
def dashboard():
    return "Logged in."

if __name__ == "__main__":
    app.run(debug=True)
