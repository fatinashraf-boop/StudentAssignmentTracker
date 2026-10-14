
import os

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("012345")

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "assignments.db"


# Connect to the SQLite database
def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Create the database and table automatically
def init_db():
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK(status IN ('Pending', 'Completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Display dashboard and assignments
@app.route("/")
def home():
    with get_db_connection() as connection:
        assignments = connection.execute("""
            SELECT * FROM assignments
            ORDER BY due_date ASC, id DESC
        """).fetchall()

        total = connection.execute(
            "SELECT COUNT(*) FROM assignments"
        ).fetchone()[0]

        pending = connection.execute("""
            SELECT COUNT(*) FROM assignments
            WHERE status = 'Pending'
        """).fetchone()[0]

        completed = connection.execute("""
            SELECT COUNT(*) FROM assignments
            WHERE status = 'Completed'
        """).fetchone()[0]

    return render_template(
        "index.html",
        assignments=assignments,
        total=total,
        pending=pending,
        completed=completed
    )


# Add a new assignment
@app.route("/add", methods=["POST"])
def add_assignment():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    due_date = request.form.get("due_date", "").strip()

    if not title or not subject or not due_date:
        flash("Please complete all assignment fields.", "error")
        return redirect(url_for("home"))

    with get_db_connection() as connection:
        connection.execute("""
            INSERT INTO assignments (title, subject, due_date)
            VALUES (?, ?, ?)
        """, (title, subject, due_date))

    flash("Assignment added successfully.", "success")
    return redirect(url_for("home"))


# Display and save assignment edits
@app.route("/edit/<int:assignment_id>", methods=["GET", "POST"])
def edit_assignment(assignment_id):
    with get_db_connection() as connection:
        assignment = connection.execute("""
            SELECT * FROM assignments WHERE id = ?
        """, (assignment_id,)).fetchone()

        if assignment is None:
            flash("Assignment not found.", "error")
            return redirect(url_for("home"))

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            subject = request.form.get("subject", "").strip()
            due_date = request.form.get("due_date", "").strip()
            status = request.form.get("status", "")

            if (
                not title or not subject or not due_date
                or status not in ("Pending", "Completed")
            ):
                flash("Please enter valid assignment details.", "error")
                return redirect(
                    url_for("edit_assignment", assignment_id=assignment_id)
                )

            connection.execute("""
                UPDATE assignments
                SET title = ?, subject = ?, due_date = ?, status = ?
                WHERE id = ?
            """, (title, subject, due_date, status, assignment_id))

            flash("Assignment updated successfully.", "success")
            return redirect(url_for("home"))

    return render_template("edit.html", assignment=assignment)


# Update status directly from the dashboard
@app.route("/status/<int:assignment_id>", methods=["POST"])
def update_status(assignment_id):
    status = request.form.get("status", "")

    if status not in ("Pending", "Completed"):
        flash("Invalid assignment status.", "error")
        return redirect(url_for("home"))

    with get_db_connection() as connection:
        connection.execute("""
            UPDATE assignments
            SET status = ?
            WHERE id = ?
        """, (status, assignment_id))

    flash("Assignment status updated.", "success")
    return redirect(url_for("home"))


# Delete an assignment
@app.route("/delete/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    with get_db_connection() as connection:
        connection.execute("""
            DELETE FROM assignments WHERE id = ?
        """, (assignment_id,))

    flash("Assignment deleted.", "success")
    return redirect(url_for("home"))


# Initialize the database when the app starts
init_db()

if __name__ == "__main__":
    app.run(debug=True)
