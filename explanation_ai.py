import random

def generate_explanation(resume_text, job_desc="", result=None):

    if result is None:
        result = {}

    score = float(result.get("final_score", 0))
    grade = result.get("grade", "N/A")

    text = str(resume_text).lower()

    explanation = ""

    # ---------------- VARIATION MESSAGES ---------------- #

    strong_msgs = [
        "🔥 Excellent match! Candidate is highly suitable.",
        "🚀 Outstanding profile with strong alignment.",
        "💯 Highly relevant resume for this role."
    ]

    good_msgs = [
        "✅ Good match. Meets most requirements.",
        "👍 Solid profile with decent alignment.",
        "✔ Candidate fits well with job expectations."
    ]

    moderate_msgs = [
        "⚠️ Moderate match. Some improvements needed.",
        "⚡ Average alignment. Needs enhancement.",
        "🔄 Partial match. Resume can be improved."
    ]

    weak_msgs = [
        "❌ Weak match. Resume needs significant improvement.",
        "🚫 Low relevance to job role.",
        "⚠️ Poor alignment with job requirements."
    ]

    # ---------------- SCORE BASED MESSAGE ---------------- #

    if score >= 85:
        explanation += random.choice(strong_msgs) + "\n"
    elif score >= 70:
        explanation += random.choice(good_msgs) + "\n"
    elif score >= 50:
        explanation += random.choice(moderate_msgs) + "\n"
    else:
        explanation += random.choice(weak_msgs) + "\n"

    explanation += f"\n📊 Score: {score} | Grade: {grade}\n"

    # ---------------- SKILL DETECTION ---------------- #

    skills = ["python", "java", "c++", "machine learning", "deep learning",
              "sql", "flask", "django", "react", "node", "aws"]

    found_skills = [s for s in skills if s in text]

    if found_skills:
        explanation += "\n✔ Skills Found: " + ", ".join(found_skills[:3]) + "\n"
    else:
        explanation += "\n❗ No strong technical skills detected\n"

    # ---------------- PROJECT CHECK ---------------- #

    if "project" in text:
        explanation += random.choice([
            "✔ Good project experience.",
            "✔ Projects strengthen the resume.",
            "✔ Practical work is mentioned."
        ]) + "\n"
    else:
        explanation += random.choice([
            "❗ Missing project section.",
            "❗ Add projects to improve profile.",
            "❗ No practical work shown."
        ]) + "\n"

    # ---------------- EXPERIENCE CHECK ---------------- #

    if "experience" in text or "intern" in text:
        explanation += random.choice([
            "✔ Experience section is present.",
            "✔ Some work experience detected.",
            "✔ Exposure to real-world work."
        ]) + "\n"
    else:
        explanation += random.choice([
            "❗ Add work experience.",
            "❗ No experience mentioned.",
            "❗ Include internships."
        ]) + "\n"

    # ---------------- SUGGESTIONS (RANDOMIZED) ---------------- #

    suggestions_pool = [
        "- Add more relevant technical skills",
        "- Include strong projects with description",
        "- Improve resume formatting",
        "- Customize resume for job role",
        "- Use action verbs and achievements",
        "- Add certifications",
        "- Improve summary section"
    ]

    random.shuffle(suggestions_pool)

    explanation += "\n💡 Suggestions:\n"

    for s in suggestions_pool[:4]:
        explanation += s + "\n"

    return explanation