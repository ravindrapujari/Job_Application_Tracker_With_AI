import streamlit as st
from datetime import date
from database import (
    init_db,
    add_application,
    get_applications,
    update_stage,
    delete_application,
)

# ----------------------------------------------------
# 1. Page Configuration & Database Initialization
# ----------------------------------------------------
st.set_page_config(page_title="Job Application Tracker", page_icon="💼", layout="wide")

# Ensure the database table exists
init_db()

STAGE_OPTIONS = [
    "Applied",
    "Interview Scheduled",
    "Offer Generated",
    "Offer Accepted",
    "Offer Rejected",
]

# ----------------------------------------------------
# 2. Sidebar Form to Add New Application
# ----------------------------------------------------
st.sidebar.header("➕ Add New Application")

with st.sidebar.form(key="job_application_form", clear_on_submit=True):
    company = st.text_input("Company *")
    role = st.text_input("Role *")
    salary = st.text_input("Salary")
    stage = st.selectbox("Stage", STAGE_OPTIONS)
    applied_on = st.date_input("Date Applied", value=date.today())
    link = st.text_input("Job Link")

    submit_btn = st.form_submit_button("Add Application")

    # Handle form submission and save to SQLite database
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
# 3. Main Area - Display & Manage Applications
# ----------------------------------------------------
st.title("💼 Job Application Tracker")
st.markdown("Track and manage your ongoing job applications (saved in SQLite).")

# Fetch all applications from SQLite database
applications = get_applications()

if not applications:
    st.info("No applications saved yet. Use the sidebar form to add your first job application!")
else:
    st.subheader(f"Applications List ({len(applications)})")

    # Render each application with options to update stage or delete
    for app in applications:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            # Column 1: Application Details
            with col1:
                st.markdown(f"### {app['role']} @ **{app['company']}**")
                st.write(f"📅 **Date Applied:** {app['applied_on']} | 💰 **Salary:** {app['salary']}")
                if app["link"]:
                    st.markdown(f"🔗 [View Job Posting]({app['link']})")

            # Column 2: Update Stage Dropdown
            with col2:
                current_idx = (
                    STAGE_OPTIONS.index(app["stage"])
                    if app["stage"] in STAGE_OPTIONS
                    else 0
                )
                selected_stage = st.selectbox(
                    "Stage",
                    STAGE_OPTIONS,
                    index=current_idx,
                    key=f"stage_{app['id']}",
                )
                # If stage was changed by user, update in database
                if selected_stage != app["stage"]:
                    update_stage(app["id"], selected_stage)
                    st.rerun()

            # Column 3: Delete Action
            with col3:
                st.write("")  # Spacing
                st.write("")
                if st.button("🗑️ Delete", key=f"del_{app['id']}"):
                    delete_application(app["id"])
                    st.rerun()

            st.divider()
