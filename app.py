import streamlit as st
from datetime import date

# ----------------------------------------------------
# 1. Page Configuration & State Initialization
# ----------------------------------------------------
st.set_page_config(page_title="Job Application Tracker", page_icon="💼", layout="wide")

# Initialize session state for storing job applications in memory
if "applications" not in st.session_state:
    st.session_state.applications = []

# ----------------------------------------------------
# 2. Sidebar Form to Add New Application
# ----------------------------------------------------
st.sidebar.header("➕ Add New Application")

with st.sidebar.form(key="job_application_form", clear_on_submit=True):
    company = st.text_input("Company *")
    role = st.text_input("Role *")
    salary = st.text_input("Salary")
    stage = st.selectbox(
        "Stage",
        [
            "Applied",
            "Interview Scheduled",
            "Offer Generated",
            "Offer Accepted",
            "Offer Rejected",
        ],
    )
    date_applied = st.date_input("Date Applied", value=date.today())
    job_link = st.text_input("Job Link")

    submit_btn = st.form_submit_button("Add Application")

    # Form submission logic
    if submit_btn:
        if company.strip() and role.strip():
            new_application = {
                "company": company.strip(),
                "role": role.strip(),
                "salary": salary.strip() if salary.strip() else "N/A",
                "stage": stage,
                "date_applied": str(date_applied),
                "job_link": job_link.strip(),
            }
            # Append new application to session state
            st.session_state.applications.append(new_application)
            st.sidebar.success(f"Added application for {company}!")
        else:
            st.sidebar.error("Please provide both Company and Role.")

# ----------------------------------------------------
# 3. Main Area - Display Applications List
# ----------------------------------------------------
st.title("💼 Job Application Tracker")
st.markdown("Track and manage your ongoing job applications.")

applications = st.session_state.applications

if not applications:
    st.info("No applications added yet. Use the sidebar form to add your first job application!")
else:
    st.subheader(f"Applications List ({len(applications)})")

    # Iterate and display each application as an item
    for idx, app in enumerate(reversed(applications), start=1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {app['role']} @ **{app['company']}**")
                st.write(f"📅 **Date Applied:** {app['date_applied']} | 💰 **Salary:** {app['salary']}")
                if app["job_link"]:
                    st.markdown(f"🔗 [View Job Posting]({app['job_link']})")
            with col2:
                st.info(f"**Stage:** {app['stage']}")
            st.divider()
