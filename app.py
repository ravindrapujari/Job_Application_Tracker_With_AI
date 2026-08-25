import streamlit as st
from datetime import date
import importlib
import database

# Reload database module to ensure updates are reflected in active Streamlit sessions
importlib.reload(database)

from database import (
    init_db,
    add_application,
    get_applications,
    get_stats,
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
# 3. Main Area - Dashboard Metrics
# ----------------------------------------------------
st.title("💼 Job Application Dashboard")

# Fetch calculated counts from database.py
stats = get_stats()

# Metric cards
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(label="Total Applications", value=stats["total"])
col2.metric(label="Interviews", value=stats["interviews"])
col3.metric(label="Offers Accepted", value=stats["offers_accepted"])
col4.metric(label="Offers Rejected", value=stats["offers_rejected"])
col5.metric(label="Response Rate", value=f"{stats['response_rate']:.1f}%")

st.divider()

# ----------------------------------------------------
# 4. Main Area - Filtered Applications List
# ----------------------------------------------------
applications = get_applications(stage=selected_filter, search_query=search_query)

st.subheader(f"Applications ({len(applications)})")

if not applications:
    st.info("No matching applications found.")
else:
    for app in applications:
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 1])

            # Column 1: Application Information
            with c1:
                st.markdown(f"### {app['role']} @ **{app['company']}**")
                st.write(f"📅 **Date Applied:** {app['applied_on']} | 💰 **Salary:** {app['salary']}")
                if app["link"]:
                    st.markdown(f"🔗 [View Job Posting]({app['link']})")

            # Column 2: Immediate Stage Update Dropdown
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

            # Column 3: Delete Button
            with c3:
                st.write("")  # Vertical spacing
                st.write("")
                if st.button("🗑️ Delete", key=f"delete_btn_{app['id']}"):
                    delete_application(app["id"])
                    st.rerun()

            st.divider()
