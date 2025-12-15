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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT username, role FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    conn.close()

    return f"""
        <h2>Dashboard</h2>
        <p>Welcome, <strong>{user['username']}</strong></p>
        <p>Your role: <strong>{user['role']}</strong></p>

        <hr>

        <ul>
            <li><a href="/notes">View Notes</a></li>
            <li><a href="/notes/create">Create Note</a></li>
            <li><a href="/admin">Admin Panel</a></li>
            <li><a href="/logout">Logout</a></li>
        </ul>
    """



@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access denied", 403

    conn = get_db_connection()
    notes = conn.execute(
        """
        SELECT notes.id, title, content, username
        FROM notes
        JOIN users ON notes.user_id = users.id
        """
    ).fetchall()
    conn.close()

    notes_html = ""
    for note in notes:
        notes_html += f"""
            <div style="border:1px solid red; padding:10px; margin:10px 0;">
                <p><strong>Note ID:</strong> {note['id']}</p>
                <p><strong>User:</strong> {note['username']}</p>
                <h4>{note['title']}</h4>
                <p>{note['content']}</p>
                <a href="/notes/delete/{note['id']}">Delete Note</a>
            </div>
        """

    return f"""
        <h2>Admin Panel</h2>
        <p>Administrative view of all notes</p>

        {notes_html}

        <br>
        <a href="/dashboard">Back to Dashboard</a>
    """



#here I will implement CRUD Functions 
# Create Notes 
@app.route("/notes/create", methods=["GET", "POST"])
def create_note():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)",
            (title, content, session["user_id"])
        )
        conn.commit()
        conn.close()

        return redirect("/notes")

    return """
        <h2>Create Note</h2>
        <form method="post">
            Title:<br>
            <input name="title"><br><br>
            Content:<br>
            <textarea name="content"></textarea><br><br>
            <button type="submit">Create</button>
        </form>
    """
#view notes func here 

@app.route("/notes")
def view_notes():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    if session.get("role") == "admin":
        notes = conn.execute(
            "SELECT notes.id, title, content, username FROM notes JOIN users ON notes.user_id = users.id"
        ).fetchall()
    else:
        notes = conn.execute(
            "SELECT id, title, content FROM notes WHERE user_id=?",
            (session["user_id"],)
        ).fetchall()

    conn.close()

    notes_html = ""
    for note in notes:
        notes_html += f"""
            <div style='border:1px solid #ccc; padding:10px; margin:10px 0;'>
                <h3>{note['title']}</h3>
                <p>{note['content']}</p>
            </div>
        """

    return f"""
    <h2>Your Notes</h2>

    <a href="/notes/create">Create New Note</a> |
    <a href="/dashboard">Back to Dashboard</a>
    <br><br>

    {notes_html}

    """

#Delete Func
@app.route("/notes/delete/<int:note_id>")
def delete_note(note_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    note = conn.execute(
        "SELECT * FROM notes WHERE id=?",
        (note_id,)
    ).fetchone()

    if not note:
        conn.close()
        return "Note not found", 404

    # Ownership check + admin override
    if note["user_id"] != session["user_id"] and session.get("role") != "admin":
        conn.close()
        return "Access denied", 403

    conn.execute(
        "DELETE FROM notes WHERE id=?",
        (note_id,)
    )
    conn.commit()
    conn.close()

    return redirect("/notes")

if __name__ == "__main__":
    app.run(debug=True)


