from flask import Flask, request, redirect, session
import sqlite3
import re
import html
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"


# --------------------
# Helpers
# --------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def valid_password(password):
    if len(password) < 8 or len(password) > 20:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*()_+=\-]", password):
        return False
    return True

def set_message(msg):
    session["message"] = msg

def get_message():
    return session.pop("message", None)

def page(content):
    message = get_message()
    message_html = f"<p style='color:green;'>{html.escape(message)}</p>" if message else ""
    return f"""
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .container {{ max-width: 800px; margin: auto; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        button {{ padding: 6px 12px; }}
    </style>
    <div class="container">
        {message_html}
        {content}
    </div>
    """


# --------------------
# Landing
# --------------------
@app.route("/")
def home():
    return redirect("/dashboard") if "user_id" in session else redirect("/login")


# --------------------
# Register
# --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not valid_password(password):
            return page("""
                <p>Password must be 8–20 chars and include a letter, number, and special character.</p>
                <a href="/register">Try again</a>
            """)

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, "user")
            )
            conn.commit()
            conn.close()
            set_message("Account created successfully.")
            return redirect("/login")

        except sqlite3.IntegrityError:
            conn.close()
            return page("""
                <p>Username already exists.</p>
                <a href="/register">Try again</a>
            """)

    return page("""
        <h2>Register</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Register</button>
        </form>
        <p>Already have an account? <a href="/login">Login here</a></p>
    """)


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

        return page("<p>Invalid credentials.</p><a href='/login'>Try again</a>")

    return page("""
        <h2>Login</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Login</button>
        </form>
        <p>No account? <a href="/register">Register here</a></p>
    """)


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

    return page(f"""
        <h2>Dashboard</h2>
        <p>Welcome, <strong>{html.escape(user['username'])}</strong></p>
        <p>Role: <strong>{html.escape(user['role'])}</strong></p>
        <ul>
            <li><a href="/notes">View Notes</a></li>
            <li><a href="/notes/create">Create Note</a></li>
            {admin_link}
            <li><a href="/logout">Logout</a></li>
        </ul>
    """)


# --------------------
# Admin Panel
# --------------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        set_message("Permission denied.")
        return redirect("/dashboard")

    conn = get_db_connection()
    notes = conn.execute("""
        SELECT notes.id, title, content, username
        FROM notes JOIN users ON notes.user_id = users.id
    """).fetchall()

    users = conn.execute(
        "SELECT id, username, role FROM users"
    ).fetchall()
    conn.close()

    notes_html = "".join([
        f"""
        <div style='border:1px solid red; padding:10px; margin:10px;'>
            <p><strong>{html.escape(n['username'])}</strong></p>
            <h4>{html.escape(n['title'])}</h4>
            <p>{html.escape(n['content'])}</p>
            <a href='/notes/delete/{n['id']}'>Delete Note</a>
        </div>
        """
        for n in notes
    ])

    users_html = "".join([
        f"<p>{html.escape(u['username'])} ({html.escape(u['role'])}) " +
        (f"<a href='/admin/delete_user/{u['id']}'>Delete</a>" if u["role"] != "admin" else "") +
        "</p>"
        for u in users
    ])

    return page(f"""
        <h2>Admin Panel</h2>
        <h3>Notes</h3>
        {notes_html}
        <h3>Users</h3>
        {users_html}
        <a href="/dashboard">Back to Dashboard</a>
    """)


@app.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):
    if session.get("role") != "admin":
        set_message("Permission denied.")
        return redirect("/dashboard")

    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id=? AND role!='admin'", (user_id,))
    conn.commit()
    conn.close()

    set_message("User deleted.")
    return redirect("/admin")


# --------------------
# Notes CRUD
# --------------------
@app.route("/notes")
def view_notes():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    notes = conn.execute(
        "SELECT id, title, content FROM notes WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    notes_html = "".join([
        f"""
        <div style='border:1px solid #ccc; padding:10px; margin:10px;'>
            <h3>{html.escape(n['title'])}</h3>
            <p>{html.escape(n['content'])}</p>
            <a href='/notes/edit/{n['id']}'>Edit</a> |
            <a href='/notes/delete/{n['id']}'>Delete</a>
        </div>
        """
        for n in notes
    ])

    return page(f"""
        <h2>Your Notes</h2>
        <a href="/notes/create">Create Note</a> |
        <a href="/dashboard">Dashboard</a>
        {notes_html}
    """)


@app.route("/notes/create", methods=["GET", "POST"])
def create_note():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)",
            (request.form["title"], request.form["content"], session["user_id"])
        )
        conn.commit()
        conn.close()
        set_message("Note created.")
        return redirect("/notes")

    return page("""
        <h2>Create Note</h2>
        <form method="post">
            Title:<br><input name="title"><br>
            Content:<br><textarea name="content"></textarea><br>
            <button type="submit">Create</button>
        </form>
    """)


@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    conn = get_db_connection()
    note = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()

    if not note or note["user_id"] != session.get("user_id"):
        conn.close()
        set_message("Permission denied.")
        return redirect("/notes")

    if request.method == "POST":
        conn.execute(
            "UPDATE notes SET title=?, content=? WHERE id=?",
            (request.form["title"], request.form["content"], note_id)
        )
        conn.commit()
        conn.close()
        set_message("Note updated.")
        return redirect("/notes")

    conn.close()
    return page(f"""
        <h2>Edit Note</h2>
        <form method="post">
            <input name="title" value="{html.escape(note['title'])}"><br>
            <textarea name="content">{html.escape(note['content'])}</textarea><br>
            <button type="submit">Update</button>
        </form>
    """)


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
        set_message("Note not found.")
        return redirect("/notes")

    # Owner OR admin can delete
    if note["user_id"] != session.get("user_id") and session.get("role") != "admin":
        conn.close()
        set_message("Permission denied.")
        return redirect("/dashboard")

    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()

    set_message("Note deleted.")
    return redirect("/notes")



if __name__ == "__main__":
    app.run(debug=True)
