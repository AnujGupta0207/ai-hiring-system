from flask import Flask, render_template, request, redirect, session, Response
import os
import sqlite3
import PyPDF2
import utils.advanced_ranker as ar
from database import init_db
from explanation_ai import generate_explanation

app = Flask(__name__)
app.secret_key = "supersecurekey123"

# 🔥 FIX FOR RENDER DEPLOYMENT
UPLOAD_FOLDER = "/tmp/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

init_db()


# ---------------- PDF TEXT EXTRACTION ---------------- #
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
    return text


# ---------------- LOGIN ---------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["user"] = "admin"
            return redirect("/jobs")
        else:
            return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ---------------- HOME (FIXED) ---------------- #
@app.route("/")
def home():
    if "user" in session:
        return redirect("/jobs")
    return redirect("/login")


# ---------------- JOB LIST ---------------- #
@app.route("/jobs")
def jobs():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hiring.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, job_description FROM jobs ORDER BY id DESC")
    jobs = cursor.fetchall()

    conn.close()

    return render_template("jobs.html", jobs=jobs)


# ---------------- CREATE JOB ---------------- #
@app.route("/create-job", methods=["GET", "POST"])
def create_job():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        job_details = request.form["job_details"]

        conn = sqlite3.connect("hiring.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO jobs (job_description) VALUES (?)", (job_details,))
        conn.commit()
        conn.close()

        return redirect("/jobs")

    return render_template("create_job.html")


# ---------------- DELETE JOB ---------------- #
@app.route("/delete-job/<int:job_id>")
def delete_job(job_id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hiring.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM candidates WHERE job_id=?", (job_id,))
    cursor.execute("DELETE FROM jobs WHERE id=?", (job_id,))

    conn.commit()
    conn.close()

    return redirect("/jobs")


# ---------------- UPLOAD RESUME ---------------- #
@app.route("/upload/<int:job_id>", methods=["GET", "POST"])
def upload_resume(job_id):

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        # Get job description
        conn = sqlite3.connect("hiring.db")
        cursor = conn.cursor()
        cursor.execute("SELECT job_description FROM jobs WHERE id=?", (job_id,))
        job_row = cursor.fetchone()
        conn.close()

        if not job_row:
            return "Job not found"

        job_description = job_row[0]

        # Form data
        candidate_name = request.form.get("candidate_name")
        resume_text = request.form.get("resume_text", "")
        file = request.files.get("resume_file")

        # File upload
        if file and file.filename != "":
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            resume_text = extract_text_from_pdf(filepath)
            name = candidate_name if candidate_name else file.filename
        else:
            name = candidate_name if candidate_name else "Typed Resume"

        # ---------------- AI SCORING ---------------- #
        result = ar.score_resume(resume_text, job_description)

        final_score = float(result.get("final_score", 0))

        # 🔥 EXTRA BOOST FIX (OPTIONAL BUT GOOD)
        final_score = min(final_score * 1.1 + 5, 100)

        # 🔥 UPDATED GRADE
        if final_score >= 85:
            grade = "A+"
        elif final_score >= 75:
            grade = "A"
        elif final_score >= 65:
            grade = "B"
        elif final_score >= 50:
            grade = "C"
        else:
            grade = "Reject"

        feedback = " | ".join(result.get("feedback", ["No feedback"]))
        recommendation = result.get("recommendation", "No recommendation")

        # Save DB
        conn = sqlite3.connect("hiring.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO candidates (job_id, name, score, grade, feedback, recommendation)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            name,
            final_score,
            grade,
            feedback,
            recommendation
        ))

        conn.commit()
        conn.close()

        return redirect(f"/dashboard/{job_id}")

    return render_template("upload_resume.html", job_id=job_id)


# ---------------- DASHBOARD ---------------- #
@app.route("/dashboard/<int:job_id>")
def dashboard(job_id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hiring.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, score, grade, feedback, recommendation
    FROM candidates
    WHERE job_id=?
    ORDER BY score DESC
    """, (job_id,))

    candidates = cursor.fetchall()

    enhanced = []

    for c in candidates:
        name, score, grade, feedback, recommendation = c

        explanation = generate_explanation(
            feedback,
            "",
            {"final_score": score, "grade": grade}
        )

        enhanced.append((name, score, grade, feedback, recommendation, explanation))

    candidates = enhanced

    total = len(candidates)

    if total > 0:
        scores = [c[1] for c in candidates]
        grades = [c[2] for c in candidates]

        avg_score = round(sum(scores) / total, 2)
        highest_score = max(scores)
        lowest_score = min(scores)

        grade_counts = {}
        for g in grades:
            grade_counts[g] = grade_counts.get(g, 0) + 1
    else:
        avg_score = highest_score = lowest_score = 0
        grade_counts = {}

    conn.close()

    return render_template(
        "dashboard.html",
        candidates=candidates,
        job_id=job_id,
        total_candidates=total,
        avg_score=avg_score,
        highest_score=highest_score,
        lowest_score=lowest_score,
        grade_counts=grade_counts
    )


# ---------------- EXPORT CSV ---------------- #
@app.route("/export/<int:job_id>")
def export(job_id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hiring.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, score, grade, recommendation
    FROM candidates
    WHERE job_id=?
    ORDER BY score DESC
    """, (job_id,))

    candidates = cursor.fetchall()
    conn.close()

    def generate():
        yield "Name,Score,Grade,Recommendation\n"
        for c in candidates:
            yield f"{c[0]},{c[1]},{c[2]},{c[3]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=ranking.csv"}
    )


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)