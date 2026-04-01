import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# LOAD MODEL
classifier = pickle.load(open("model/resume_classifier.pkl", "rb"))
vectorizer_model = pickle.load(open("model/vectorizer.pkl", "rb"))

# SKILLS
SKILLS_DB = [
    "python","java","c++","javascript","django","flask","react",
    "machine learning","deep learning","nlp","data science",
    "sql","mongodb","aws","docker","kubernetes","cloud","api"
]

def extract_skills(text):
    text = text.lower()
    return [s for s in SKILLS_DB if s in text]

def extract_experience(text):
    match = re.search(r'(\d+)\+?\s*(years|yrs)', text.lower())
    return int(match.group(1)) if match else 0

def extract_education_score(text):
    text = text.lower()
    if "phd" in text:
        return 100
    elif "master" in text or "m.tech" in text:
        return 85
    elif "bachelor" in text or "b.tech" in text:
        return 70
    return 50

def calculate_grade(score):
    if score >= 85: return "A+"
    elif score >= 75: return "A"
    elif score >= 65: return "B"
    elif score >= 50: return "C"
    return "Reject"

def score_resume(resume_text, job_description):

    resume_text = resume_text.lower()
    job_description = job_description.lower()

    # 1️⃣ CATEGORY (NO NEGATIVE NOW 🔥)
    resume_vec = vectorizer_model.transform([resume_text])
    predicted = classifier.predict(resume_vec)[0]

    category_score = 10  # fixed baseline

    # 2️⃣ SKILLS (IMPROVED)
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)

    match = len(set(resume_skills) & set(job_skills))
    total = len(job_skills) if job_skills else 1

    skill_score = (match / total) * 100  # % based

    # 3️⃣ SIMILARITY (BOOSTED 🔥)
    tfidf = TfidfVectorizer(stop_words="english")
    vectors = tfidf.fit_transform([resume_text, job_description])

    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    similarity_score = min(similarity * 120, 100)  # boosted

    # 4️⃣ EXPERIENCE
    exp = extract_experience(resume_text)
    experience_score = min(exp * 15, 100)

    # 5️⃣ EDUCATION
    education_score = extract_education_score(resume_text)

    # 6️⃣ PROJECT
    keywords = ["project","developed","built","designed","implemented"]
    project_score = min(sum(k in resume_text for k in keywords) * 10, 100)

    # 🎯 FINAL WEIGHTED SCORE
    final_score = (
        similarity_score * 0.35 +
        skill_score * 0.25 +
        experience_score * 0.15 +
        education_score * 0.10 +
        project_score * 0.10 +
        category_score * 0.05
    )

    # 🔥 BASE BOOST
    final_score += 10

    final_score = round(min(final_score, 100), 2)

    grade = calculate_grade(final_score)

    # FEEDBACK
    feedback = []

    if skill_score < 40:
        feedback.append("Improve required skills.")
    else:
        feedback.append("Strong skill match.")

    if exp < 2:
        feedback.append("Low experience.")
    elif exp < 5:
        feedback.append("Moderate experience.")
    else:
        feedback.append("Highly experienced.")

    if similarity_score < 40:
        feedback.append("Resume not aligned with job.")
    else:
        feedback.append("Good job alignment.")

    if education_score >= 80:
        feedback.append("Strong education.")

    if final_score >= 85:
        recommendation = "Strongly Recommended"
    elif final_score >= 70:
        recommendation = "Recommended"
    elif final_score >= 55:
        recommendation = "Consider"
    else:
        recommendation = "Not Recommended"

    return {
        "final_score": final_score,
        "grade": grade,
        "feedback": feedback,
        "recommendation": recommendation
    }