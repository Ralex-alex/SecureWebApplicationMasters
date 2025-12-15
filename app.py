from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# --------------------
# Landing Page
# --------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


# --------------------
# Register
# --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, "user")
            )
            conn.commit()
            conn.close()
            return redirect("/login")

        except sqlite3.IntegrityError:
            conn.close()
            return """
                <p>Username already exists.</p>
                <a href="/register">Try again</a>
            """

    return """
        <h2>Register</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Register</button>
        </form>
        <p>Already have an account? <a href="/login">Login here</a></p>
    """



# --------------------
# Login
# --------------------
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

        return "<p>Invalid credentials</p><a href='/login'>Try again</a>"

    return """
        <h2>Login</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Login</button>
        </form>
        <p>No account? <a href="/register">Register here</a></p>
    """


# --------------------
# Logout
# --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# --------------------
# Dashboard
# --------------------
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

    admin_link = "<li><a href='/admin'>Admin Panel</a></li>" if user["role"] == "admin" else ""

    return f"""
        <h2>Dashboard</h2>
        <p>Welcome, <strong>{user['username']}</strong></p>
        <p>Role: <strong>{user['role']}</strong></p>
        <hr>
        <ul>
            <li><a href="/notes">View Notes</a></li>
            <li><a href="/notes/create">Create Note</a></li>
            {admin_link}
            <li><a href="/logout">Logout</a></li>
        </ul>
    """


# --------------------
# Admin Panel
# --------------------
@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "<h3>Access denied</h3>", 403

    conn = get_db_connection()
    notes = conn.execute("""
        SELECT notes.id, title, content, username
        FROM notes
        JOIN users ON notes.user_id = users.id
    """).fetchall()
    conn.close()

    notes_html = ""
    for note in notes:
        notes_html += f"""
            <div style="border:1px solid red; padding:10px; margin:10px;">
                <p><strong>ID:</strong> {note['id']}</p>
                <p><strong>User:</strong> {note['username']}</p>
                <h4>{note['title']}</h4>
                <p>{note['content']}</p>
                <a href="/notes/delete/{note['id']}">Delete</a>
            </div>
        """

    return f"""
        <h2>Admin Panel</h2>
        <p>Administrative view of all notes</p>
        {notes_html}
        <a href="/dashboard">Back to Dashboard</a>
    """


# --------------------
# Create Note
# --------------------
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
        <a href="/dashboard">Back to Dashboard</a>
    """


# --------------------
# View Notes
# --------------------
@app.route("/notes")
def view_notes():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    if session.get("role") == "admin":
        notes = conn.execute(
            "SELECT id, title, content FROM notes"
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
            <div style="border:1px solid #ccc; padding:10px; margin:10px;">
                <h3>{note['title']}</h3>
                <p>{note['content']}</p>
                <a href="/notes/edit/{note['id']}">Edit</a> |
                <a href="/notes/delete/{note['id']}">Delete</a>
            </div>
        """

    return f"""
        <h2>Your Notes</h2>
        <a href="/notes/create">Create Note</a> |
        <a href="/dashboard">Dashboard</a>
        <br><br>
        {notes_html}
    """


# --------------------
# Edit Note
# --------------------
@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):
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

    if note["user_id"] != session["user_id"] and session.get("role") != "admin":
        conn.close()
        return "Access denied", 403

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        conn.execute(
            "UPDATE notes SET title=?, content=? WHERE id=?",
            (title, content, note_id)
        )
        conn.commit()
        conn.close()
        return redirect("/notes")

    conn.close()

    return f"""
        <h2>Edit Note</h2>
        <form method="post">
            Title:<br>
            <input name="title" value="{note['title']}"><br><br>
            Content:<br>
            <textarea name="content">{note['content']}</textarea><br><br>
            <button type="submit">Update</button>
        </form>
        <a href="/notes">Cancel</a>
    """


# --------------------
# Delete Note 
# --------------------
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

    if note["user_id"] != session["user_id"] and session.get("role") != "admin":
        conn.close()
        return "Access denied", 403

    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()

    return redirect("/notes")


if __name__ == "__main__":
    app.run(debug=True)
