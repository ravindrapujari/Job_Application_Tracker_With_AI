import re
import json
import os
import streamlit as st
import httpx
from google import genai

# ----------------------------------------------------
# 1. Curated List of ~50 Common Tech Skills (Keyword Mode)
# ----------------------------------------------------
TECH_SKILLS = [
    # Programming Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", 
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
    
    # Web & Frameworks
    "React", "Node.js", "Next.js", "Vue", "Angular", "FastAPI", "Django", 
    "Flask", "Spring Boot", "Express", "HTML", "CSS", "REST API", "GraphQL",
    
    # Cloud & DevOps
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "CI/CD", "Terraform", 
    "Linux", "Git", "Jenkins",
    
    # Data & Databases
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Snowflake", "BigQuery", 
    "Spark", "Kafka",
    
    # AI, ML & Data Science
    "AI", "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", 
    "Pandas", "NumPy", "Scikit-Learn", "NLP", "LLM"
]

# ----------------------------------------------------
# 2. Keyword Matching Functions (No AI/API)
# ----------------------------------------------------
def extract_skills(text: str) -> list[str]:
    """
    Extracts tech skills present in a given job description text using keyword regex matching.
    """
    if not text or not text.strip():
        return []

    found_skills = []
    for skill in TECH_SKILLS:
        escaped_skill = re.escape(skill)
        pattern = rf"(?<![a-zA-Z0-9]){escaped_skill}(?![a-zA-Z0-9])"
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill)

    return found_skills

def analyze_skills_match(job_skills: list[str] | str, user_skills: list[str] | str) -> dict:
    """
    Compares the skills found in a job description against the user's skills using set operations.
    """
    if isinstance(job_skills, str):
        target_skills = extract_skills(job_skills)
    else:
        target_skills = list(dict.fromkeys(job_skills))

    if isinstance(user_skills, str):
        user_skills_list = [s.strip() for s in user_skills.split(",") if s.strip()]
    else:
        user_skills_list = [str(s).strip() for s in user_skills if str(s).strip()]

    user_skills_lower = {s.lower() for s in user_skills_list}

    matched_skills = []
    missing_skills = []

    for skill in target_skills:
        if skill.lower() in user_skills_lower:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    total_required = len(target_skills)
    match_score = (len(matched_skills) / total_required * 100.0) if total_required > 0 else 0.0

    return {
        "match_score": round(match_score, 1),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }

# ----------------------------------------------------
# 3. AI Analysis with Gemini / Groq API
# ----------------------------------------------------
def clean_json_response(raw_text: str) -> str:
    """Strips markdown code fences (```json ... ```) from model output."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()

def analyze_with_gemini(job_description: str, user_skills: list[str] | str) -> dict:
    """
    Sends the job description and user skills to Gemini (gemini-2.5-flash) using google-genai,
    or to Groq if a Groq API key (gsk_...) is provided in st.secrets["GROQ_API_KEY"].
    
    Returns structured JSON with required_skills, matched_skills, missing_skills, score, and summary.
    """
    # Read API key from st.secrets["GROQ_API_KEY"]
    api_key = None
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "API key not found. Please add 'GROQ_API_KEY' to .streamlit/secrets.toml"
        )

    # Format user skills
    if isinstance(user_skills, list):
        user_skills_str = ", ".join(user_skills)
    else:
        user_skills_str = str(user_skills)

    prompt = f"""
You are an expert technical career advisor.
Analyze the following job description and compare it with the candidate's skills.

Job Description:
\"\"\"{job_description}\"\"\"

Candidate's Skills:
\"\"\"{user_skills_str}\"\"\"

Reply with ONLY a valid JSON object (no markdown, no preamble, no backticks, no code fences) with this exact schema:
{{
    "required_skills": ["list of key technical & relevant skills required by the job"],
    "matched_skills": ["list of required skills the user already possesses"],
    "missing_skills": ["list of required skills the user is missing"],
    "score": 75,
    "summary": "Two sentence concise summary of the candidate's match and advice."
}}
"""

    # If the key is a Groq key (starts with 'gsk_'), route to Groq's high-speed API endpoint
    if api_key.startswith("gsk_"):
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            },
            timeout=30.0,
        )
        if response.status_code != 200:
            # Fallback to other available models on Groq if model name changes
            fallback_res = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen/qwen3.6-27b",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=30.0,
            )
            if fallback_res.status_code == 200:
                raw_output = fallback_res.json()["choices"][0]["message"]["content"]
            else:
                raise RuntimeError(f"Groq API Error: {response.text}")
        else:
            raw_output = response.json()["choices"][0]["message"]["content"]
    else:
        # Standard Google Gemini API via google-genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw_output = response.text or ""

    # Clean markdown fences and parse JSON
    cleaned_json_str = clean_json_response(raw_output)
    return json.loads(cleaned_json_str)
