import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import os

# --- CONFIGURATION ---
# Use relative paths so this works on any computer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'bible_plan.csv')
PROGRESS_FILE = os.path.join(BASE_DIR, 'user_progress.csv')

# CHECK YOUR YEAR: Did you mean 2025?
START_DATE = datetime.date(2026, 1, 1)

# --- SETUP & DATA LOADING ---
st.set_page_config(page_title="The Year of the Word", page_icon="📖", layout="centered")


def load_data():
    # ERROR HANDLING: Check if file actually exists before crashing
    if not os.path.exists(DATA_FILE):
        st.error(f"File not found: {DATA_FILE}. Make sure it is in the same folder as this script.")
        st.stop()

    # CRITICAL: If using the asterisk file, use sep='*'.
    # If you saved it as a standard comma CSV, remove sep='*'.
    try:
        plan_df = pd.read_csv(DATA_FILE, sep='*')
    except Exception as e:
        st.error(f"Error reading CSV. Are you sure it's a CSV and not an Excel file renamed? Error: {e}")
        st.stop()

    # Load or Create User Progress File
    if not os.path.exists(PROGRESS_FILE):
        # Initialize with all False
        plan_df['Completed'] = False
        plan_df['Date_Completed'] = None
        # Save as standard CSV (comma separated) for the progress file to keep it simple
        plan_df.to_csv(PROGRESS_FILE, index=False)
        return plan_df
    else:
        return pd.read_csv(PROGRESS_FILE)


def save_progress(df):
    df.to_csv(PROGRESS_FILE, index=False)


# Load data into session state
if 'df' not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# --- DASHBOARD HEADER ---
st.title("📖 52-Week Bible Tracker")
today = datetime.date.today()

# Logic check: If today is before start date, don't show negative days
if today < START_DATE:
    st.warning("You haven't started yet! The clock starts Jan 1.")
    day_of_year = 0
    current_week = 0
else:
    day_of_year = (today - START_DATE).days + 1
    current_week = (day_of_year // 7) + 1

# Calculate metrics
total_weeks = 52
completed_weeks = df['Completed'].sum()
progress_pct = completed_weeks / total_weeks

# --- KPI ROW ---
col1, col2, col3 = st.columns(3)
col1.metric("Current Week", f"Week {current_week}", f"Day {day_of_year}")
col2.metric("Progress", f"{completed_weeks} / {total_weeks}", f"{int(progress_pct * 100)}%")
col3.metric("Status", "On Track" if completed_weeks >= current_week - 1 else "Behind",
            delta_color="normal" if completed_weeks >= current_week - 1 else "inverse")

st.progress(progress_pct)

# --- THE TRACKER ---
st.subheader("Weekly Checklist")

with st.form("tracker_form"):
    for index, row in df.iterrows():
        week_num = row['Week']
        # Handle cases where columns might be read as different types
        reading = str(row['Reading Range'])
        focus = str(row['Focus'])

        label = f"**Wk {week_num}**: {reading} ({focus})"
        is_checked = st.checkbox(label, value=bool(row['Completed']), key=f"chk_{week_num}")

        df.at[index, 'Completed'] = is_checked
        if is_checked and not row['Completed']:
            df.at[index, 'Date_Completed'] = str(datetime.date.today())

    submitted = st.form_submit_button("Update Progress")
    if submitted:
        save_progress(df)
        st.success("Progress Saved!")
        st.rerun()

# --- ANALYTICS ---
st.divider()
st.subheader("Burndown Chart")

weeks = list(range(1, 53))
ideal_progress = weeks
actual_progress = []

running_total = 0
for w in weeks:
    # Ensure we don't crash if week index is out of bounds
    if w <= len(df) and df.iloc[w - 1]['Completed']:
        running_total += 1
    actual_progress.append(running_total)

fig = go.Figure()
fig.add_trace(
    go.Scatter(x=weeks, y=ideal_progress, mode='lines', name='Ideal Pace', line=dict(dash='dash', color='gray')))
fig.add_trace(
    go.Scatter(x=weeks, y=actual_progress, mode='lines+markers', name='Actual Progress', line=dict(color='blue')))
fig.update_layout(title="Ideal vs. Actual Completion", xaxis_title="Week", yaxis_title="Weeks Completed")
st.plotly_chart(fig)