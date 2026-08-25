import streamlit as st
from datetime import date
import importlib
import database
import analyzer

# Ensure modules are freshly reloaded in active Streamlit sessions
importlib.reload(database)
importlib.reload(analyzer)

from database import (
    init_db,
    add_application,
    get_applications,
    get_stats,
    update_stage,
    delete_application,
)
from analyzer import (
    TECH_SKILLS,
    extract_skills,
    analyze_skills_match,
    analyze_with_gemini,
)

# ----------------------------------------------------
# 1. Page Configuration & Database Initialization
# ----------------------------------------------------
st.set_page_config(page_title="Job Application Tracker & Analyzer", page_icon="💼", layout="wide")

# Ensure the database table exists
init_db()

STAGE_OPTIONS = [
    "Applied",
    "Interview Scheduled",
    "Offer Generated",
    "Offer Accepted",
    "Offer Rejected",
]

# Callback to immediately save stage changes in SQLite
def handle_stage_change(app_id):
    new_val = st.session_state.get(f"stage_select_{app_id}")
    if new_val:
        update_stage(app_id, new_val)

# ----------------------------------------------------
# 2. Sidebar - Form, Filters & Search
# ----------------------------------------------------
st.sidebar.title("💼 Job Tracker")

# --- Filter & Search Section ---
st.sidebar.subheader("🔍 Filter & Search")
selected_filter = st.sidebar.selectbox("Filter by Stage", ["All"] + STAGE_OPTIONS)
search_query = st.sidebar.text_input("Search Company or Role", placeholder="e.g. Google, Frontend")

st.sidebar.divider()

# --- Add Application Form ---
st.sidebar.subheader("➕ Add New Application")
with st.sidebar.form(key="job_application_form", clear_on_submit=True):
    company = st.text_input("Company *")
    role = st.text_input("Role *")
    salary = st.text_input("Salary")
    stage = st.selectbox("Stage", STAGE_OPTIONS)
    applied_on = st.date_input("Date Applied", value=date.today())
    link = st.text_input("Job Link")

    submit_btn = st.form_submit_button("Add Application")

    if submit_btn:
        if company.strip() and role.strip():
            add_application(
                company=company.strip(),
                role=role.strip(),
                salary=salary.strip() if salary.strip() else "N/A",
                stage=stage,
                applied_on=str(applied_on),
                link=link.strip(),
            )
            st.sidebar.success(f"Added application for {company}!")
            st.rerun()
        else:
            st.sidebar.error("Please provide both Company and Role.")

# ----------------------------------------------------
# 3. Main Screen - Tabs for Tracker & Analyzer
# ----------------------------------------------------
st.title("💼 Job Application Hub")

tab_tracker, tab_analyzer = st.tabs(["📋 Applications Tracker", "🎯 Job Description Analyzer"])

# ====================================================
# TAB 1: Applications Tracker & Dashboard
# ====================================================
with tab_tracker:
    # --- Dashboard Metrics ---
    stats = get_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(label="Total Applications", value=stats["total"])
    col2.metric(label="Interviews", value=stats["interviews"])
    col3.metric(label="Offers Accepted", value=stats["offers_accepted"])
    col4.metric(label="Offers Rejected", value=stats["offers_rejected"])
    col5.metric(label="Response Rate", value=f"{stats['response_rate']:.1f}%")

    st.divider()

    # --- Applications List ---
    applications = get_applications(stage=selected_filter, search_query=search_query)

    st.subheader(f"Applications List ({len(applications)})")

    if not applications:
        st.info("No matching applications found.")
    else:
        for app in applications:
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 1])

                # Application Details
                with c1:
                    st.markdown(f"### {app['role']} @ **{app['company']}**")
                    st.write(f"📅 **Date Applied:** {app['applied_on']} | 💰 **Salary:** {app['salary']}")
                    if app["link"]:
                        st.markdown(f"🔗 [View Job Posting]({app['link']})")

                # Change Stage Dropdown (saves immediately)
                with c2:
                    current_idx = (
                        STAGE_OPTIONS.index(app["stage"])
                        if app["stage"] in STAGE_OPTIONS
                        else 0
                    )
                    st.selectbox(
                        "Change Stage",
                        STAGE_OPTIONS,
                        index=current_idx,
                        key=f"stage_select_{app['id']}",
                        on_change=handle_stage_change,
                        args=(app["id"],),
                    )

                # Delete Button
                with c3:
                    st.write("")  # Vertical alignment spacing
                    st.write("")
                    if st.button("🗑️ Delete", key=f"delete_btn_{app['id']}"):
                        delete_application(app["id"])
                        st.rerun()

                st.divider()

# ====================================================
# TAB 2: Job Description Analyzer (Keyword & AI Modes)
# ====================================================
with tab_analyzer:
    st.subheader("🎯 Job Description & Skill Matcher")
    st.markdown("Analyze job requirements and compare them against your skillset using local keyword matching or Gemini AI.")

    # Mode Selector
    analysis_mode = st.radio(
        "Select Analysis Engine:",
        ["⚡ Keyword Match (Instant / Local)", "✨ AI Analysis (Gemini 2.5 Flash)"],
        horizontal=True,
    )

    col_jd, col_user = st.columns(2)

    with col_jd:
        jd_input = st.text_area(
            "📋 Paste Job Description Here",
            height=240,
            placeholder="e.g. We are looking for a Senior Software Engineer with strong experience in Python, FastAPI, Docker, and AWS...",
        )

    with col_user:
        selected_skills = st.multiselect(
            "🛠️ Select Your Tech Skills",
            options=TECH_SKILLS,
            default=["Python", "SQL", "Docker", "Git"],
        )
        custom_skills = st.text_input(
            "➕ Or add custom skills (comma-separated)",
            placeholder="e.g. GraphQL, Tailwind, CI/CD",
        )

    # Combine selected and typed skills
    combined_user_skills = list(selected_skills)
    if custom_skills.strip():
        typed_skills = [s.strip() for s in custom_skills.split(",") if s.strip()]
        combined_user_skills.extend(typed_skills)

    if st.button("🔍 Analyze Skills Match", type="primary"):
        if not jd_input.strip():
            st.warning("Please paste a job description first.")
        else:
            if "Keyword Match" in analysis_mode:
                # 1. Local Keyword Matching Mode
                extracted_job_skills = extract_skills(jd_input)

                if not extracted_job_skills:
                    st.warning("No known tech skills detected in this job description. Try adding more detailed text.")
                else:
                    analysis = analyze_skills_match(extracted_job_skills, combined_user_skills)

                    st.markdown("### 📊 Analysis Results (Keyword Engine)")
                    score = analysis["match_score"]
                    st.metric("🎯 Match Score", f"{score}%")
                    st.progress(score / 100.0)

                    res_col1, res_col2, res_col3 = st.columns(3)
                    with res_col1:
                        st.success(f"✅ **Skills You Have ({len(analysis['matched_skills'])})**")
                        for s in analysis["matched_skills"]:
                            st.write(f"- {s}")
                    with res_col2:
                        st.error(f"❌ **Missing Skills ({len(analysis['missing_skills'])})**")
                        for s in analysis["missing_skills"]:
                            st.write(f"- {s}")
                    with res_col3:
                        st.info(f"📋 **Detected Job Skills ({len(extracted_job_skills)})**")
                        for s in extracted_job_skills:
                            st.write(f"- {s}")

            else:
                # 2. Gemini AI Analysis Mode
                with st.spinner("🤖 Analyzing with Gemini 2.5 Flash..."):
                    try:
                        ai_result = analyze_with_gemini(jd_input, combined_user_skills)

                        st.markdown("### 📊 AI Analysis Results (Gemini 2.5 Flash)")
                        
                        score = float(ai_result.get("score", 0))
                        st.metric("🎯 AI Match Score", f"{score}%")
                        st.progress(min(max(score / 100.0, 0.0), 1.0))

                        # Two-sentence summary
                        summary = ai_result.get("summary", "")
                        if summary:
                            st.info(f"💡 **AI Summary:** {summary}")

                        res_col1, res_col2, res_col3 = st.columns(3)
                        
                        matched = ai_result.get("matched_skills", [])
                        missing = ai_result.get("missing_skills", [])
                        required = ai_result.get("required_skills", [])

                        with res_col1:
                            st.success(f"✅ **Skills You Have ({len(matched)})**")
                            for s in matched:
                                st.write(f"- {s}")

                        with res_col2:
                            st.error(f"❌ **Missing Skills ({len(missing)})**")
                            for s in missing:
                                st.write(f"- {s}")

                        with res_col3:
                            st.info(f"📋 **Required Skills ({len(required)})**")
                            for s in required:
                                st.write(f"- {s}")

                    except Exception as e:
                        st.error(f"⚠️ AI Analysis Error: {str(e)}")
