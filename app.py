# -*- coding: utf-8 -*-
"""
app.py -- Streamlit Dashboard
==============================
MDM Mini Project: Typing Speed Before and After Practice

HOW STREAMLIT WORKS (beginner note)
------------------------------------
Streamlit re-runs this ENTIRE script from top to bottom every time a
user interacts with ANY widget (button, slider, text input, etc.).

This means regular Python variables are reset on every interaction.
To remember values across re-runs, we use  st.session_state  -- a
special dictionary that persists as long as the browser tab is open.
Think of it as the app's short-term memory.

HOW THIS FILE IS ORGANISED
---------------------------
Section 1  -- Imports
Section 2  -- Page configuration (must be the FIRST Streamlit call)
Section 3  -- Custom CSS for the academic analytics look
Section 4  -- Demo data (10 realistic students, clearly labelled)
Section 5  -- Session-state initialisation
Section 6  -- Shared helpers (run analysis, convert data, build cards)
Section 7  -- Page: Overview
Section 8  -- Page: Student Data (manual entry + CSV upload)
Section 9  -- Page: Visualizations
Section 10 -- Page: Statistical Analysis
Section 11 -- Page: Conclusion & Export
Section 12 -- Main function (sidebar + page router)

TO RUN THIS APP
---------------
Open a terminal in the project folder and run:

    streamlit run app.py

If you have multiple Python versions, use the full path to the one
where the libraries are installed:

    C:\\Users\\vedmu\\AppData\\Local\\Programs\\Python\\Python311\\python.exe -m streamlit run app.py
"""

# =============================================================================
# SECTION 1 -- IMPORTS
# =============================================================================
import copy          # Used to deep-copy demo data so the original is never modified
import io            # Used to build in-memory CSV files for download buttons

import pandas as pd  # For reading uploaded CSV files and building display tables
import plotly.graph_objects as go   # Fine-grained Plotly chart control
from plotly.subplots import make_subplots  # (not used directly; kept for future use)
import streamlit as st

# Import our own statistics module -- this is the one we built in Milestone 2.
# Both files live in the same folder, so Python can find it automatically.
from statistics_analysis import analyse, DataValidationError


# =============================================================================
# SECTION 2 -- PAGE CONFIGURATION
# =============================================================================
# This MUST be the very first Streamlit call in the script.
# Setting layout="wide" uses the full browser width.
st.set_page_config(
    page_title="Typing Speed Analysis | MDM Project",
    page_icon="⌨️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "MDM Mini Project -- Typing Speed Before & After Practice"
    },
)


# =============================================================================
# SECTION 3 -- CUSTOM CSS
# =============================================================================
# st.markdown with unsafe_allow_html=True lets us inject raw HTML/CSS into
# the page. We keep the styling minimal and academic -- clean whitespace,
# consistent typography, subtle shadows. No heavy animations.
st.markdown(
    """
    <style>
    /* ── Global font & background ─────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.95rem;
        padding: 4px 0;
    }

    /* ── Metric / KPI cards ───────────────────────────────────────────── */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 20px 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-top: 4px solid #3B82F6;
        margin-bottom: 8px;
    }
    .kpi-card.amber  { border-top-color: #F59E0B; }
    .kpi-card.green  { border-top-color: #10B981; }
    .kpi-card.purple { border-top-color: #8B5CF6; }

    .kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748B;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E293B;
        line-height: 1.1;
    }
    .kpi-unit {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-left: 4px;
    }

    /* ── Section headers ──────────────────────────────────────────────── */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 4px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E2E8F0;
    }
    .section-sub {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 20px;
    }

    /* ── Data-source badge ────────────────────────────────────────────── */
    .badge-demo {
        display: inline-block;
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
        border-radius: 4px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-real {
        display: inline-block;
        background: #D1FAE5;
        color: #065F46;
        border: 1px solid #6EE7B7;
        border-radius: 4px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* ── Stat rows in analysis page ───────────────────────────────────── */
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #F1F5F9;
        align-items: center;
    }
    .stat-name  { font-weight: 500; color: #334155; font-size: 0.92rem; }
    .stat-value { font-weight: 700; color: #1E293B; font-size: 1.05rem; }
    .stat-note  { font-size: 0.78rem; color: #94A3B8; margin-top: 2px; }

    /* ── Conclusion box ───────────────────────────────────────────────── */
    .conclusion-box {
        background: #F0FDF4;
        border-left: 4px solid #10B981;
        border-radius: 6px;
        padding: 20px 24px;
        margin: 16px 0;
        line-height: 1.7;
        color: #1E293B;
    }
    .conclusion-box.reject {
        background: #EFF6FF;
        border-left-color: #3B82F6;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# SECTION 4 -- DEMO DATA
# =============================================================================
# This dataset is used ONLY when the user has not entered their own data.
# It is clearly labelled as "Sample / Demo Data" everywhere it appears.
# Values are realistic WPM measurements for undergraduate CS students.

DEMO_RECORDS = [
    {"id": "S01", "name": "Aanya Sharma",  "before": 42.0, "after": 55.0},
    {"id": "S02", "name": "Rahul Mehta",   "before": 38.0, "after": 50.0},
    {"id": "S03", "name": "Priya Iyer",    "before": 60.0, "after": 71.0},
    {"id": "S04", "name": "Dev Patel",     "before": 55.0, "after": 63.0},
    {"id": "S05", "name": "Sneha Rao",     "before": 30.0, "after": 44.0},
    {"id": "S06", "name": "Arjun Kumar",   "before": 48.0, "after": 57.0},
    {"id": "S07", "name": "Meera Nair",    "before": 65.0, "after": 73.0},
    {"id": "S08", "name": "Karan Singh",   "before": 35.0, "after": 47.0},
    {"id": "S09", "name": "Divya Reddy",   "before": 52.0, "after": 62.0},
    {"id": "S10", "name": "Rohan Gupta",   "before": 44.0, "after": 56.0},
]


# =============================================================================
# SECTION 5 -- SESSION STATE INITIALISATION
# =============================================================================
# These lines run every time the script re-runs, but the `if` guard means
# the assignment only happens ONCE -- on the very first page load.
# After that, Streamlit preserves the existing values across interactions.

if "records" not in st.session_state:
    # Start with demo data so the dashboard is never empty for a first-time visitor.
    st.session_state.records = copy.deepcopy(DEMO_RECORDS)

if "data_source" not in st.session_state:
    # Tracks whether the current data is "demo", "manual", or "csv".
    st.session_state.data_source = "demo"


# =============================================================================
# SECTION 6 -- SHARED HELPERS
# =============================================================================

# ── 6a. Chart color palette ───────────────────────────────────────────────────
# Using a consistent palette across all charts makes the dashboard feel cohesive.
C_BEFORE  = "#3B82F6"   # Blue -- before-practice values
C_AFTER   = "#F59E0B"   # Amber -- after-practice values
C_POS     = "#10B981"   # Green -- positive improvement
C_NEG     = "#EF4444"   # Red   -- negative change (got slower)
C_GRID    = "#F1F5F9"   # Very light gray for chart backgrounds
C_TEXT    = "#334155"   # Dark slate for axis labels

# Shared Plotly layout defaults applied to every chart
CHART_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color=C_TEXT, size=12),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter"),
)


def get_analysis():
    """
    Run the statistical analysis on the current session data.

    Returns
    -------
    (results, error_message)
      results       : dict from statistics_analysis.analyse()  -- or None on error
      error_message : str describing the problem               -- or None on success

    WHY a helper function?
    ----------------------
    Multiple pages need the analysis results. Rather than repeating the
    try/except block in every page, we centralise it here. Any page can call
    get_analysis() and check whether results is None.
    """
    try:
        # analyse() is imported from statistics_analysis.py.
        # It validates the data and returns every statistic we need.
        results = analyse(st.session_state.records)
        return results, None
    except DataValidationError as e:
        return None, str(e)


def records_to_df() -> pd.DataFrame:
    """
    Convert the current session records (list of dicts) to a display DataFrame.

    The analysis module uses keys "id", "before", "after".
    The dashboard also stores an optional "name" key for display purposes.
    This function builds a clean, human-readable table from both.
    """
    rows = []
    for rec in st.session_state.records:
        rows.append({
            "Student ID":   rec.get("id",     ""),
            "Name":         rec.get("name",   "--"),
            "Before (WPM)": rec.get("before", 0),
            "After (WPM)":  rec.get("after",  0),
            "Change (WPM)": round(rec.get("after", 0) - rec.get("before", 0), 1),
        })
    return pd.DataFrame(rows)


def source_badge() -> str:
    """Return an HTML badge indicating whether data is demo or real."""
    if st.session_state.data_source == "demo":
        return '<span class="badge-demo">⚠ Sample Data</span>'
    return '<span class="badge-real">✓ Your Data</span>'


def kpi_card(label: str, value: str, unit: str = "", color: str = "") -> str:
    """Return HTML for a styled KPI metric card."""
    color_class = {"amber": "amber", "green": "green", "purple": "purple"}.get(color, "")
    return f"""
    <div class="kpi-card {color_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
    </div>
    """


def apply_chart_defaults(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply consistent layout defaults to any Plotly figure."""
    fig.update_layout(**CHART_LAYOUT, title=dict(text=title, font=dict(size=14, color=C_TEXT)))
    fig.update_xaxes(gridcolor=C_GRID, linecolor="#E2E8F0", tickfont=dict(size=11))
    fig.update_yaxes(gridcolor=C_GRID, linecolor="#E2E8F0", tickfont=dict(size=11))
    return fig


# =============================================================================
# SECTION 7 -- PAGE: OVERVIEW
# =============================================================================

def page_overview():
    """
    Overview page: four KPI cards + a quick comparison bar chart.

    PURPOSE
    -------
    Gives the user a snapshot of the most important numbers at a glance
    before they dive into the detailed analysis pages.

    DATA FLOW
    ---------
    1. Call get_analysis() to get the full results dict.
    2. Extract the four headline numbers (n, mean_before, mean_after, mean_diff).
    3. Render them as styled HTML cards.
    4. Render a simple bar chart showing the before/after comparison.
    """
    # Header
    st.markdown('<div class="section-header">📊 Overview</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">Summary of all students in the current dataset. '
        f'{source_badge()}</div>',
        unsafe_allow_html=True,
    )

    results, error = get_analysis()

    if error:
        st.error(f"**Could not compute statistics:** {error}")
        st.info("Go to **Student Data** to add or fix your data.")
        return

    # ── KPI cards ─────────────────────────────────────────────────────────────
    # We use 4 equal columns; each column holds one metric card.
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            kpi_card("Students", str(results["n"]), " pairs"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card("Mean Speed -- Before", f"{results['mean_before']:.1f}", " WPM", ""),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            kpi_card("Mean Speed -- After", f"{results['mean_after']:.1f}", " WPM", "amber"),
            unsafe_allow_html=True,
        )
    with c4:
        sign = "+" if results["mean_diff"] >= 0 else ""
        st.markdown(
            kpi_card("Mean Improvement", f"{sign}{results['mean_diff']:.1f}", " WPM", "green"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Overview chart: grouped before/after bar ───────────────────────────────
    # This gives an at-a-glance view of every student's progress.
    # Each student gets two bars (before = blue, after = amber).
    left, right = st.columns([2, 1])

    with left:
        ids   = results["ids"]
        names = [r.get("name", sid) for r, sid in zip(st.session_state.records, ids)]
        labels = [f"{sid}" for sid in ids]  # short labels for x-axis

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name="Before Practice",
            x=labels,
            y=results["before"].tolist(),
            marker_color=C_BEFORE,
            text=[f"{v:.0f}" for v in results["before"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Before: %{y} WPM<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="After Practice",
            x=labels,
            y=results["after"].tolist(),
            marker_color=C_AFTER,
            text=[f"{v:.0f}" for v in results["after"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>After: %{y} WPM<extra></extra>",
        ))

        fig.update_layout(
            barmode="group",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Typing Speed (WPM)",
            xaxis_title="Student ID",
        )
        apply_chart_defaults(fig, "Before vs After Typing Speed -- All Students")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        # Significance result card
        pval  = results["p_value"]
        sig   = results["significant"]
        alpha = results["alpha"]

        if pval is not None:
            p_str = f"{pval:.4f}"
            verdict = "**Significant** ✅" if sig else "**Not Significant** ❌"
            color   = "#D1FAE5" if sig else "#FEE2E2"
            border  = "#10B981" if sig else "#EF4444"
        else:
            p_str   = "N/A"
            verdict = "Cannot compute"
            color   = "#F1F5F9"
            border  = "#94A3B8"

        st.markdown(
            f"""
            <div style="background:{color};border-left:4px solid {border};
                        border-radius:8px;padding:18px;margin-top:8px;">
                <div style="font-size:0.75rem;font-weight:600;color:#64748B;
                            text-transform:uppercase;letter-spacing:0.06em;">
                    Hypothesis Test
                </div>
                <div style="font-size:1.1rem;margin:8px 0;">{verdict}</div>
                <div style="font-size:0.85rem;color:#475569;">
                    p-value = {p_str}<br>
                    alpha = {alpha}<br>
                    df = {results['df']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Quick stats mini-table
        st.markdown("**Quick Stats**")
        quick = {
            "Mean diff (d_bar)": f"{results['mean_diff']:+.2f} WPM",
            "SD of diffs":    f"{results['std_diff']:.2f}",
            "t-statistic":    f"{results['t_statistic']:.4f}" if results["t_statistic"] else "N/A",
        }
        for k, v in quick.items():
            st.markdown(
                f'<div class="stat-row"><span class="stat-name">{k}</span>'
                f'<span class="stat-value">{v}</span></div>',
                unsafe_allow_html=True,
            )


# =============================================================================
# SECTION 8 -- PAGE: STUDENT DATA
# =============================================================================

def page_student_data():
    """
    Student Data page: manual entry form, CSV upload, and data table.

    HOW IT WORKS
    ------------
    All entered data lives in  st.session_state.records  -- a list of dicts.
    Every interaction (Add, Delete, Upload) modifies this list and then
    Streamlit re-runs the script, automatically refreshing every other page.

    THREE TABS
    ----------
    Tab 1 -- Add Entry   : Form to enter one student at a time.
    Tab 2 -- Upload CSV  : Upload a file to replace the whole dataset.
    Tab 3 -- View & Edit : Display the current table + delete a student.
    """
    st.markdown('<div class="section-header">📝 Student Data</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">Add or upload student measurements. '
        f'{source_badge()}</div>',
        unsafe_allow_html=True,
    )

    tab_add, tab_csv, tab_view = st.tabs(
        ["➕ Add Entry", "📤 Upload CSV", "🗂 View & Edit Data"]
    )

    # ── Tab 1: Manual entry ───────────────────────────────────────────────────
    with tab_add:
        st.markdown("Enter one student's measurements below.")
        st.caption(
            "If this is your first manual entry, the demo data will be cleared "
            "and replaced with your real data."
        )

        # st.form groups widgets together and only triggers a re-run when the
        # submit button is pressed -- preventing needless re-runs on every keystroke.
        with st.form("add_student_form", clear_on_submit=True):
            col_a, col_b, col_c, col_d = st.columns([1.2, 2, 1.5, 1.5])

            with col_a:
                new_id = st.text_input(
                    "Student ID *",
                    placeholder="e.g. S11",
                    help="A unique identifier for this student (required).",
                )
            with col_b:
                new_name = st.text_input(
                    "Name (optional)",
                    placeholder="e.g. Vikram Bose",
                    help="Display name -- not used in calculations.",
                )
            with col_c:
                new_before = st.number_input(
                    "Before WPM *",
                    min_value=1.0,
                    max_value=300.0,
                    value=None,
                    step=0.5,
                    format="%.1f",
                    help="Typing speed BEFORE the practice session.",
                    placeholder="e.g. 45.0",
                )
            with col_d:
                new_after = st.number_input(
                    "After WPM *",
                    min_value=1.0,
                    max_value=300.0,
                    value=None,
                    step=0.5,
                    format="%.1f",
                    help="Typing speed AFTER the practice session.",
                    placeholder="e.g. 58.0",
                )

            submitted = st.form_submit_button("Add Student", type="primary")

        if submitted:
            # Validate the form fields before adding
            errors = []
            if not new_id or not new_id.strip():
                errors.append("Student ID cannot be empty.")
            if new_before is None:
                errors.append("Before WPM is required.")
            if new_after is None:
                errors.append("After WPM is required.")

            if not errors:
                sid = new_id.strip()
                # Check for duplicate ID in current dataset
                existing_ids = [r["id"] for r in st.session_state.records]
                if sid in existing_ids:
                    st.error(
                        f"Student ID '{sid}' already exists. "
                        "Each student must have a unique ID."
                    )
                else:
                    # If currently on demo data, switch to real data mode first.
                    if st.session_state.data_source == "demo":
                        st.session_state.records = []
                        st.session_state.data_source = "manual"

                    st.session_state.records.append({
                        "id":     sid,
                        "name":   new_name.strip() if new_name else "--",
                        "before": float(new_before),
                        "after":  float(new_after),
                    })
                    st.success(f"✅ Student '{sid}' added. Total: {len(st.session_state.records)} students.")
                    st.rerun()
            else:
                for e in errors:
                    st.error(e)

    # ── Tab 2: CSV upload ─────────────────────────────────────────────────────
    with tab_csv:
        st.markdown(
            "Upload a CSV file to load your entire dataset at once. "
            "**This replaces the current data.**"
        )

        # Show the required format
        with st.expander("📋 Required CSV format"):
            st.markdown(
                """
                Your CSV must have at least these three columns (names are flexible):

                | id  | name           | before | after |
                |-----|----------------|--------|-------|
                | S01 | Aanya Sharma   | 42     | 55    |
                | S02 | Rahul Mehta    | 38     | 50    |

                - **id** -- unique student identifier (required)
                - **name** -- student name (optional, for display only)
                - **before** -- WPM before practice (required, must be > 0)
                - **after** -- WPM after practice (required, must be > 0)

                Column names are case-insensitive and can include spaces.
                """
            )

        # Download the demo file as a template
        demo_df = records_to_df() if st.session_state.data_source == "demo" else None

        # Provide a blank template download
        template_csv = "id,name,before,after\nS01,Student Name,45,58\n"
        st.download_button(
            label="⬇ Download CSV Template",
            data=template_csv,
            file_name="typing_speed_template.csv",
            mime="text/csv",
        )

        st.markdown("---")
        uploaded = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            help="Select the CSV file containing your typing speed data.",
        )

        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)

                # Normalise column names: lowercase, strip whitespace
                df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

                # Accept common column name variations
                col_map = {}
                for col in df.columns:
                    if "id" in col:
                        col_map[col] = "id"
                    elif "name" in col:
                        col_map[col] = "name"
                    elif "before" in col:
                        col_map[col] = "before"
                    elif "after" in col:
                        col_map[col] = "after"
                df = df.rename(columns=col_map)

                # Check required columns are present
                missing = [c for c in ["id", "before", "after"] if c not in df.columns]
                if missing:
                    st.error(
                        f"Missing required columns: {missing}. "
                        "Your CSV must contain 'id', 'before', and 'after' columns."
                    )
                else:
                    # Preview the data before committing
                    st.markdown("**Preview (first 5 rows):**")
                    st.dataframe(df.head(), use_container_width=True)

                    # Try to parse into records and validate via the analysis module
                    candidate_records = []
                    for _, row in df.iterrows():
                        candidate_records.append({
                            "id":     str(row["id"]).strip(),
                            "name":   str(row["name"]).strip() if "name" in df.columns else "--",
                            "before": row["before"],
                            "after":  row["after"],
                        })

                    # Validate by running the full analysis -- this will raise
                    # DataValidationError if anything is wrong.
                    _, val_error = (
                        lambda r: (analyse(r), None)
                        if True else (None, None)
                    )(candidate_records)

                    # Use a proper try/except for validation
                    try:
                        analyse(candidate_records)
                        # If we reach here, validation passed
                        if st.button("✅ Confirm & Load This Data", type="primary"):
                            st.session_state.records = candidate_records
                            st.session_state.data_source = "csv"
                            st.success(
                                f"Loaded {len(candidate_records)} student records from CSV."
                            )
                            st.rerun()
                    except DataValidationError as ve:
                        st.error(f"**Validation failed:** {ve}")

            except Exception as ex:
                st.error(f"Could not read the file: {ex}")

    # ── Tab 3: View & Edit Data ───────────────────────────────────────────────
    with tab_view:
        df = records_to_df()
        n  = len(st.session_state.records)

        col_info, col_actions = st.columns([3, 1])
        with col_info:
            st.markdown(f"**{n} student(s)** in the current dataset. {source_badge()}", unsafe_allow_html=True)

        with col_actions:
            if st.button("🔄 Reset to Demo Data"):
                st.session_state.records     = copy.deepcopy(DEMO_RECORDS)
                st.session_state.data_source = "demo"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Display the data table (read-only)
        st.dataframe(
            df.style.format({
                "Before (WPM)": "{:.1f}",
                "After (WPM)":  "{:.1f}",
                "Change (WPM)": "{:+.1f}",
            }).applymap(
                lambda v: "color: #10B981; font-weight: 600"
                if isinstance(v, (int, float)) and v > 0
                else ("color: #EF4444; font-weight: 600"
                      if isinstance(v, (int, float)) and v < 0
                      else ""),
                subset=["Change (WPM)"],
            ),
            use_container_width=True,
            hide_index=True,
        )

        # Delete a student
        st.markdown("---")
        st.markdown("**Remove a student from the dataset:**")
        existing_ids = [r["id"] for r in st.session_state.records]

        if existing_ids:
            col_sel, col_del = st.columns([2, 1])
            with col_sel:
                id_to_delete = st.selectbox(
                    "Select Student ID to remove",
                    options=existing_ids,
                    label_visibility="collapsed",
                )
            with col_del:
                if st.button("🗑 Remove", type="secondary"):
                    st.session_state.records = [
                        r for r in st.session_state.records if r["id"] != id_to_delete
                    ]
                    if st.session_state.data_source == "demo":
                        st.session_state.data_source = "manual"
                    st.success(f"Removed student '{id_to_delete}'.")
                    st.rerun()
        else:
            st.info("No students in the dataset. Add some in the '➕ Add Entry' tab.")


# =============================================================================
# SECTION 9 -- PAGE: VISUALIZATIONS
# =============================================================================

def page_visualizations():
    """
    Visualizations page: four complementary Plotly charts.

    CHART DESCRIPTIONS
    ------------------
    1. Grouped Bar  -- Mean before vs mean after (group-level view).
    2. Scatter Plot -- Each student as a point (before=x, after=y).
                      The diagonal line y=x marks "no change".
                      Points above the line → improved.
    3. Bar Chart    -- Individual improvement per student (after-before).
                      Green = improved, Red = declined.
    4. Box Plot     -- Spread of scores. Shows median, quartiles, and outliers.

    WHY FOUR CHARTS?
    ----------------
    Each chart answers a different question:
    • "Did the group improve on average?"         → Grouped bar
    • "Who improved and by how much?"             → Scatter
    • "What was each person's exact change?"      → Improvement bar
    • "How spread out are the speeds?"            → Box plot
    """
    st.markdown('<div class="section-header">📈 Visualizations</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">Interactive charts -- hover for details. '
        f'{source_badge()}</div>',
        unsafe_allow_html=True,
    )

    results, error = get_analysis()

    if error:
        st.error(f"**Cannot generate charts:** {error}")
        st.info("Go to **Student Data** to add or fix your data.")
        return

    ids    = results["ids"]
    before = results["before"]
    after  = results["after"]
    diffs  = results["differences"]
    names  = [r.get("name", sid) for r, sid in zip(st.session_state.records, ids)]
    hover  = [f"{n} ({sid})" for n, sid in zip(names, ids)]

    # ── Chart 1 & 2 (top row) ─────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        # --- Chart 1: Grouped Bar -- individual student before vs after ---
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            name="Before",
            x=ids,
            y=before.tolist(),
            marker_color=C_BEFORE,
            hovertemplate="<b>%{x}</b><br>Before: %{y:.1f} WPM<extra></extra>",
        ))
        fig1.add_trace(go.Bar(
            name="After",
            x=ids,
            y=after.tolist(),
            marker_color=C_AFTER,
            hovertemplate="<b>%{x}</b><br>After: %{y:.1f} WPM<extra></extra>",
        ))
        fig1.update_layout(
            barmode="group",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Typing Speed (WPM)",
            xaxis_title="Student ID",
        )
        apply_chart_defaults(fig1, "Before & After Typing Speed per Student")
        st.plotly_chart(fig1, use_container_width=True)
        st.caption(
            "Each student has two bars. Blue = speed before practice, "
            "Amber = speed after practice."
        )

    with col2:
        # --- Chart 2: Scatter -- before (x) vs after (y) with y=x reference ---
        # The diagonal line represents "no change" (after = before).
        # Points above the line improved; points below declined.
        axis_min = min(before.min(), after.min()) - 5
        axis_max = max(before.max(), after.max()) + 5

        fig2 = go.Figure()

        # Reference line y = x (no change baseline)
        fig2.add_shape(
            type="line",
            x0=axis_min, y0=axis_min,
            x1=axis_max, y1=axis_max,
            line=dict(color="#CBD5E1", width=1.5, dash="dash"),
        )
        fig2.add_annotation(
            x=axis_max - 2, y=axis_max - 4,
            text="No change (y = x)",
            showarrow=False,
            font=dict(size=10, color="#94A3B8"),
        )

        fig2.add_trace(go.Scatter(
            x=before.tolist(),
            y=after.tolist(),
            mode="markers+text",
            text=ids,
            textposition="top center",
            textfont=dict(size=10),
            marker=dict(
                color=[C_POS if d >= 0 else C_NEG for d in diffs],
                size=10,
                line=dict(color="white", width=1.5),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Before: %{x:.1f} WPM<br>"
                "After: %{y:.1f} WPM<br>"
                "Change: %{customdata:+.1f} WPM<extra></extra>"
            ),
            customdata=diffs.tolist(),
            name="Students",
        ))

        fig2.update_layout(
            xaxis=dict(title="Before WPM", range=[axis_min, axis_max]),
            yaxis=dict(title="After WPM",  range=[axis_min, axis_max]),
            showlegend=False,
        )
        apply_chart_defaults(fig2, "Before vs After (per Student) -- Scatter Plot")
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "Points above the dashed line improved; below the line means slower after practice. "
            "Green = improved, Red = declined."
        )

    # ── Chart 3 & 4 (bottom row) ──────────────────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        # --- Chart 3: Improvement bar -- (after - before) per student ---
        bar_colors = [C_POS if d >= 0 else C_NEG for d in diffs]

        fig3 = go.Figure(go.Bar(
            x=ids,
            y=diffs.tolist(),
            marker_color=bar_colors,
            text=[f"{d:+.1f}" for d in diffs],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Improvement: %{y:+.1f} WPM<extra></extra>"
            ),
        ))

        # Horizontal zero line
        fig3.add_hline(y=0, line_color="#94A3B8", line_width=1)

        fig3.update_layout(
            yaxis_title="WPM Change (After - Before)",
            xaxis_title="Student ID",
        )
        apply_chart_defaults(fig3, "Individual WPM Improvement per Student")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(
            "Positive bars (green) = student typed faster after practice. "
            "Negative bars (red) = student typed slower."
        )

    with col4:
        # --- Chart 4: Box plots -- distribution of before & after speeds ---
        # A box plot shows the median (middle line), the interquartile range
        # (the box itself), and outliers (individual dots).
        fig4 = go.Figure()

        fig4.add_trace(go.Box(
            y=before.tolist(),
            name="Before",
            marker_color=C_BEFORE,
            boxmean=True,           # Show mean as a dashed line inside the box
            hovertemplate="Before WPM<br>%{y:.1f}<extra></extra>",
        ))
        fig4.add_trace(go.Box(
            y=after.tolist(),
            name="After",
            marker_color=C_AFTER,
            boxmean=True,
            hovertemplate="After WPM<br>%{y:.1f}<extra></extra>",
        ))

        fig4.update_layout(
            yaxis_title="Typing Speed (WPM)",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        apply_chart_defaults(fig4, "Speed Distribution -- Before vs After")
        st.plotly_chart(fig4, use_container_width=True)
        st.caption(
            "The box spans the middle 50% of scores (IQR). The line inside is the median. "
            "The dashed line is the mean. Dots outside the whiskers are outliers."
        )


# =============================================================================
# SECTION 10 -- PAGE: STATISTICAL ANALYSIS
# =============================================================================

def page_statistical_analysis():
    """
    Statistical Analysis page: every statistic with plain-language explanations.

    DESIGN PRINCIPLE
    ----------------
    The formulas and logic already live in statistics_analysis.py.
    This page only DISPLAYS the results -- it does NOT duplicate the maths.
    Explanations are written in plain English, suitable for a beginner.
    """
    st.markdown('<div class="section-header">🔬 Statistical Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">All computed statistics with explanations. '
        f'{source_badge()}</div>',
        unsafe_allow_html=True,
    )

    results, error = get_analysis()

    if error:
        st.error(f"**Cannot compute statistics:** {error}")
        st.info("Go to **Student Data** to add or fix your data.")
        return

    # ── Row 1: Descriptive statistics + Difference statistics ─────────────────
    col_desc, col_diff = st.columns(2)

    with col_desc:
        st.markdown("#### 📐 Descriptive Statistics")
        st.markdown(
            "These numbers summarise the *raw* typing speeds in the two groups."
        )

        stats_rows = [
            ("n (paired students)",
             str(results["n"]),
             "Number of matched before/after measurements."),
            ("Mean -- Before (x_bar1)",
             f"{results['mean_before']:.4f} WPM",
             "Average speed before the practice session."),
            ("Mean -- After (x_bar2)",
             f"{results['mean_after']:.4f} WPM",
             "Average speed after the practice session."),
            ("Sample SD -- Before (s1)",
             f"{results['std_before']:.4f}",
             "Spread of before-speeds. Uses n-1 (Bessel's correction)."),
            ("Sample SD -- After (s2)",
             f"{results['std_after']:.4f}",
             "Spread of after-speeds. Uses n-1 (Bessel's correction)."),
        ]

        for name, value, note in stats_rows:
            st.markdown(
                f"""
                <div class="stat-row">
                    <div>
                        <div class="stat-name">{name}</div>
                        <div class="stat-note">{note}</div>
                    </div>
                    <div class="stat-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_diff:
        st.markdown("#### 🔁 Paired Difference Statistics")
        st.markdown(
            "Computed on **d = after - before** for each individual student."
        )

        diffs_rows = [
            ("Mean Difference (d_bar)",
             f"{results['mean_diff']:+.4f} WPM",
             "Average improvement per student. Positive = improved."),
            ("SD of Differences (s_d)",
             f"{results['std_diff']:.4f}",
             "How consistently students improved. Lower = more uniform change."),
            ("Standard Error (s_d / sqrtn)",
             f"{results['std_diff'] / (results['n'] ** 0.5):.4f} WPM",
             "Uncertainty in our estimate of d_bar. Decreases as n grows."),
        ]

        for name, value, note in diffs_rows:
            st.markdown(
                f"""
                <div class="stat-row">
                    <div>
                        <div class="stat-name">{name}</div>
                        <div class="stat-note">{note}</div>
                    </div>
                    <div class="stat-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Paired t-test results + plain-English guide ────────────────────
    col_test, col_explain = st.columns([1, 1.4])

    with col_test:
        st.markdown("#### 🧪 Paired t-Test Results")
        st.markdown(
            "Tests whether the mean improvement is real or just random noise."
        )

        t_val = results["t_statistic"]
        p_val = results["p_value"]
        alpha = results["alpha"]
        sig   = results["significant"]

        ttest_rows = [
            ("Null Hypothesis (H0)",
             "d_bar = 0",
             "Practice made no difference on average."),
            ("Alt. Hypothesis (H1)",
             "d_bar != 0",
             "Practice changed typing speed (two-tailed)."),
            ("Significance Level (alpha)",
             str(alpha),
             "We accept a 5% chance of a wrong conclusion."),
            ("t-Statistic",
             f"{t_val:.4f}" if t_val is not None else "N/A",
             "How many standard errors d_bar is from zero."),
            ("Degrees of Freedom (df)",
             str(results["df"]),
             "df = n - 1."),
            ("p-Value",
             f"{p_val:.4f}" if p_val is not None else "N/A",
             "Probability of this result if H0 were true."),
            ("Decision",
             "Reject H0 ✅" if sig else "Fail to reject H0",
             f"p {'<' if sig else '>='} alpha = {alpha}"),
        ]

        for name, value, note in ttest_rows:
            val_color = ""
            if name == "Decision":
                val_color = "color:#10B981;font-weight:700" if sig else "color:#EF4444;font-weight:700"
            st.markdown(
                f"""
                <div class="stat-row">
                    <div>
                        <div class="stat-name">{name}</div>
                        <div class="stat-note">{note}</div>
                    </div>
                    <div class="stat-value" style="{val_color}">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_explain:
        st.markdown("#### 📖 What do these numbers mean?")
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            **Why a *paired* t-test?**
            Because the same student is measured twice (before and after).
            A paired test compares each person to their *own* baseline, removing
            natural differences in typing ability between students.

            **What is the t-statistic?**
            It tells you how many standard errors the mean improvement (d_bar)
            sits away from zero. A large |t| means the improvement is large
            compared to the variability in your data -- making it unlikely to
            be a fluke.

            **What is the p-value?**
            If practice had *no effect at all*, the p-value is the probability
            of seeing an improvement at least as large as the one you measured --
            purely by random chance. A small p-value means "this improvement
            is hard to explain by luck alone."

            **The alpha = 0.05 threshold**
            We decide in advance that if p < 0.05 (a 5% chance), the result
            is "statistically significant" -- i.e., we have enough evidence to
            say practice made a real difference.
            """
        )

        # Show the student-level differences as a mini chart
        diffs = results["differences"]
        ids   = results["ids"]

        fig_mini = go.Figure(go.Bar(
            x=ids,
            y=diffs.tolist(),
            marker_color=[C_POS if d >= 0 else C_NEG for d in diffs],
            hovertemplate="<b>%{x}</b><br>d = %{y:+.1f} WPM<extra></extra>",
        ))
        fig_mini.add_hline(y=float(results["mean_diff"]),
                           line_dash="dash", line_color="#64748B",
                           annotation_text=f"d_bar = {results['mean_diff']:+.2f}",
                           annotation_position="top left")
        fig_mini.update_layout(
            height=200,
            margin=dict(l=30, r=10, t=30, b=30),
            yaxis_title="d (WPM)",
            showlegend=False,
            **{k: v for k, v in CHART_LAYOUT.items() if k not in ("margin",)},
        )
        fig_mini.update_layout(margin=dict(l=30, r=10, t=30, b=30))
        st.plotly_chart(fig_mini, use_container_width=True)
        st.caption("Individual differences (d = after - before). Dashed line = mean difference d_bar.")


# =============================================================================
# SECTION 11 -- PAGE: CONCLUSION & EXPORT
# =============================================================================

def page_conclusion_export():
    """
    Conclusion & Export page: auto-generated plain-language summary + downloads.

    AUTO-GENERATED CONCLUSION
    -------------------------
    The conclusion is built from the numerical results -- it is not a fixed
    template. If the data changes, the conclusion automatically updates.

    EXPORT OPTIONS
    --------------
    1. CSV -- the full dataset with individual differences appended.
    2. Summary text -- a plain-language report suitable for a project submission.
    """
    st.markdown('<div class="section-header">📋 Conclusion & Export</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">Plain-language interpretation and download options. '
        f'{source_badge()}</div>',
        unsafe_allow_html=True,
    )

    results, error = get_analysis()

    if error:
        st.error(f"**Cannot generate conclusion:** {error}")
        st.info("Go to **Student Data** to add or fix your data.")
        return

    # ── Auto-generated conclusion paragraph ───────────────────────────────────
    n          = results["n"]
    mean_b     = results["mean_before"]
    mean_a     = results["mean_after"]
    mean_d     = results["mean_diff"]
    std_b      = results["std_before"]
    std_a      = results["std_after"]
    std_d      = results["std_diff"]
    t_val      = results["t_statistic"]
    df         = results["df"]
    p_val      = results["p_value"]
    sig        = results["significant"]
    alpha      = results["alpha"]
    data_label = "sample" if st.session_state.data_source == "demo" else "collected"

    direction   = "increased" if mean_d > 0 else "decreased"
    direction2  = "faster" if mean_d > 0 else "slower"
    sig_word    = "statistically significant" if sig else "not statistically significant"
    h0_decision = "rejected" if sig else "not rejected"

    conclusion_text = (
        f"A paired t-test was conducted on {data_label} typing speed data from {n} student(s) "
        f"to evaluate whether a practice session produced a measurable change in WPM.\n\n"
        f"The mean typing speed before practice was {mean_b:.2f} WPM "
        f"(SD = {std_b:.2f}), and after practice it was {mean_a:.2f} WPM "
        f"(SD = {std_a:.2f}). "
        f"On average, students typed {abs(mean_d):.2f} WPM {direction2} after practice "
        f"(mean difference d_bar = {mean_d:+.2f}, SD of differences = {std_d:.2f}).\n\n"
    )

    if t_val is not None:
        conclusion_text += (
            f"The paired t-test yielded t({df}) = {t_val:.4f}, p = {p_val:.4f}. "
            f"At the significance level alpha = {alpha}, the result is {sig_word}, "
            f"and the null hypothesis (H0: d_bar = 0) was {h0_decision}.\n\n"
        )
        if sig:
            conclusion_text += (
                f"Therefore, there is sufficient statistical evidence to conclude that "
                f"the practice session {direction} typing speed. "
                f"The improvement of {abs(mean_d):.2f} WPM is unlikely to be due to "
                f"random variation alone."
            )
        else:
            conclusion_text += (
                f"Therefore, there is insufficient statistical evidence to conclude that "
                f"practice changed typing speed at the chosen significance level. "
                f"This may reflect a genuinely small effect, high variability, "
                f"or an insufficient sample size (n = {n})."
            )
    else:
        conclusion_text += (
            "The t-test could not be computed because all students showed "
            "exactly the same change, resulting in zero variance in the differences."
        )

    # Display in styled box
    box_class = "conclusion-box reject" if sig else "conclusion-box"
    conclusion_html = conclusion_text.replace("\n\n", "<br><br>")
    st.markdown(
        f'<div class="{box_class}">{conclusion_html}</div>',
        unsafe_allow_html=True,
    )

    # ── Key numbers at a glance ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Key Numbers at a Glance**")

    col_a, col_b, col_c, col_d = st.columns(4)
    glance = [
        (col_a, "Mean Before", f"{mean_b:.2f} WPM"),
        (col_b, "Mean After",  f"{mean_a:.2f} WPM"),
        (col_c, "Mean Diff",   f"{mean_d:+.2f} WPM"),
        (col_d, "p-value",     f"{p_val:.4f}" if p_val is not None else "N/A"),
    ]
    for col, label, value in glance:
        with col:
            st.metric(label=label, value=value)

    # ── Export: full data CSV ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⬇ Export Results")

    # Build the export DataFrame (adds "Change" and "Significant" columns)
    export_df = records_to_df().copy()
    export_df["Significant"] = sig
    export_df["p-value"]     = f"{p_val:.4f}" if p_val else "N/A"
    export_df["t-statistic"] = f"{t_val:.4f}" if t_val else "N/A"
    export_df["df"]          = df
    export_df["alpha"]       = alpha
    export_df["Data Source"] = data_label

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.download_button(
            label="📥 Download Full Results (CSV)",
            data=csv_bytes,
            file_name="typing_speed_results.csv",
            mime="text/csv",
            help="Downloads the student data with per-student differences and t-test summary.",
        )

    with col_e2:
        # Build a plain-text summary for the project report
        summary_text = (
            "TYPING SPEED ANALYSIS -- MDM MINI PROJECT\n"
            "=" * 50 + "\n"
            f"Data source   : {data_label.title()}\n"
            f"Students (n)  : {n}\n"
            f"Alpha (alpha)     : {alpha}\n\n"
            "DESCRIPTIVE STATISTICS\n"
            "-" * 30 + "\n"
            f"Mean Before   : {mean_b:.4f} WPM\n"
            f"Mean After    : {mean_a:.4f} WPM\n"
            f"SD Before     : {std_b:.4f}\n"
            f"SD After      : {std_a:.4f}\n\n"
            "PAIRED DIFFERENCES (after - before)\n"
            "-" * 30 + "\n"
            f"Mean diff (d_bar) : {mean_d:+.4f} WPM\n"
            f"SD of diffs   : {std_d:.4f}\n\n"
            "PAIRED t-TEST\n"
            "-" * 30 + "\n"
            f"t-statistic   : {t_val:.4f if t_val else 'N/A'}\n"
            f"df            : {df}\n"
            f"p-value       : {f'{p_val:.4f}' if p_val else 'N/A'}\n"
            f"Significant   : {'Yes' if sig else 'No'}\n\n"
            "CONCLUSION\n"
            "-" * 30 + "\n"
            + conclusion_text
        )

        st.download_button(
            label="📄 Download Summary Report (TXT)",
            data=summary_text.encode("utf-8"),
            file_name="typing_speed_summary.txt",
            mime="text/plain",
            help="Downloads a plain-text summary suitable for pasting into a project report.",
        )

    # ── Data source note ───────────────────────────────────────────────────────
    if st.session_state.data_source == "demo":
        st.warning(
            "⚠ **You are currently using Sample/Demo Data.** "
            "Go to **Student Data → Upload CSV** or **Add Entry** to load your "
            "real collected measurements before submitting your project."
        )


# =============================================================================
# SECTION 12 -- SIDEBAR + MAIN ROUTER
# =============================================================================

def main():
    """
    Entry point -- builds the sidebar navigation and routes to the correct page.

    SIDEBAR
    -------
    The sidebar shows:
      • App title and subtitle
      • Navigation menu (radio buttons -- one page active at a time)
      • Dataset status (demo vs real, student count)
      • Quick-access notes

    PAGE ROUTING
    ------------
    Streamlit radio buttons return the currently selected option as a string.
    We use a simple if/elif chain to call the appropriate page function.
    """
    with st.sidebar:
        # ── Branding ─────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center;padding:8px 0 4px;">
                <div style="font-size:2rem;">⌨️</div>
                <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;">
                    Typing Speed Analysis
                </div>
                <div style="font-size:0.75rem;color:#94A3B8;margin-top:2px;">
                    MDM Mini Project
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Navigation ────────────────────────────────────────────────────────
        page = st.radio(
            "Navigation",
            options=[
                "📊 Overview",
                "📝 Student Data",
                "📈 Visualizations",
                "🔬 Statistical Analysis",
                "📋 Conclusion & Export",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        # ── Dataset status panel ──────────────────────────────────────────────
        n = len(st.session_state.records)
        src_label = {
            "demo":   "Sample Data",
            "manual": "Manual Entry",
            "csv":    "CSV Upload",
        }.get(st.session_state.data_source, "Unknown")

        st.markdown(
            f"""
            <div style="font-size:0.78rem;color:#94A3B8;line-height:1.8;">
                <div><strong style="color:#CBD5E1;">Dataset</strong></div>
                <div>Source: {src_label}</div>
                <div>Students: {n}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.data_source == "demo":
            st.markdown(
                '<div style="background:#78350F;border-radius:6px;padding:8px 10px;'
                'font-size:0.75rem;color:#FDE68A;margin-top:8px;">'
                "⚠ Using sample data.<br>Add your real data in<br><b>Student Data</b>."
                "</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown(
            '<div style="font-size:0.72rem;color:#64748B;line-height:1.6;">'
            "📌 All charts and statistics<br>"
            "update automatically when<br>"
            "the dataset changes."
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Page router ───────────────────────────────────────────────────────────
    if page == "📊 Overview":
        page_overview()
    elif page == "📝 Student Data":
        page_student_data()
    elif page == "📈 Visualizations":
        page_visualizations()
    elif page == "🔬 Statistical Analysis":
        page_statistical_analysis()
    elif page == "📋 Conclusion & Export":
        page_conclusion_export()


# ── Script entry point ────────────────────────────────────────────────────────
# When Python runs this file directly (or Streamlit loads it),
# it calls main() to kick everything off.
if __name__ == "__main__":
    main()
else:
    # Streamlit imports this file as a module; main() must still be called.
    main()
