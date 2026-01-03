import os
from flask import Flask, request, jsonify, render_template
from google import genai
import PyPDF2
from dotenv import load_dotenv

# =====================================
# LOAD ENV VARIABLES (FORCE)
# =====================================
load_dotenv(dotenv_path=".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print("DEBUG → GEMINI_API_KEY loaded:", bool(GEMINI_API_KEY))

if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not found. Check your .env file.")

# =====================================
# FLASK APP
# =====================================
app = Flask(__name__)

# =====================================
# GEMINI CLIENT
# =====================================
client = genai.Client(api_key=GEMINI_API_KEY)

# =====================================
# PDF TEXT EXTRACTION
# =====================================
def extract_text_from_pdf(file):
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

# =====================================
# ATS ANALYSIS (UI SAFE)
# =====================================
def ats_analysis(resume_text):
    if not resume_text:
        return "ERROR: Resume text could not be extracted."

    prompt = f"""
You are a strict ATS (Applicant Tracking System).

Analyze the resume below and return ONLY in this format:

SCORE: <number>/100

CRITICAL_ISSUES:
- point 1
- point 2

MISSING_KEYWORDS:
- keyword 1
- keyword 2

RECOMMENDATIONS:
- suggestion 1
- suggestion 2

RESUME:
{resume_text[:12000]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text

# =====================================
# ROUTES
# =====================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_resume():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        # Extract text
        resume_text = extract_text_from_pdf(file)

        # ATS analysis
        result = ats_analysis(resume_text)

        return jsonify({"result": result})

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"error": "Failed to analyze resume"}), 500

# =====================================
# RUN
# =====================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)