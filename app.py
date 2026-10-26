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
    /* ── Global Font & Background ─────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background #F4F7FB */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F4F7FB !important;
        color: #17243A !important;
    }

    /* High contrast headings */
    h1, h2, h3, h4, h5, h6 {
        color: #17243A !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }

    p, span, label, div {
        color: #17243A;
    }

    /* Captions & small notes */
    .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p, small {
        color: #334155 !important;
        font-weight: 500 !important;
    }

    /* ── Sidebar: Navy #17243A ────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #17243A !important;
        border-right: 1px solid #0F172A;
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #E2E8F0 !important;
        padding: 6px 10px;
        border-radius: 6px;
        transition: all 0.15s ease-in-out;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: rgba(47, 128, 237, 0.25) !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* ── Metric / KPI Cards ───────────────────────────────────────────── */
    .kpi-card {
        background: #FFFFFF !important;
        border-radius: 12px;
        padding: 22px 24px;
        box-shadow: 0 2px 10px rgba(23, 36, 58, 0.07);
        border: 1px solid #CBD5E1;
        border-top: 5px solid #17243A;
        margin-bottom: 12px;
        transition: transform 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-card.blue   { border-top-color: #2F80ED !important; }
    .kpi-card.teal   { border-top-color: #14B8A6 !important; }
    .kpi-card.navy   { border-top-color: #17243A !important; }

    .kpi-label {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #334155 !important;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #17243A !important;
        line-height: 1.1;
    }
    .kpi-unit {
        font-size: 1rem;
        font-weight: 600;
        color: #475569 !important;
        margin-left: 5px;
    }

    /* ── Section Headers ──────────────────────────────────────────────── */
    .section-header {
        font-size: 1.5rem;
        font-weight: 800;
        color: #17243A !important;
        margin-bottom: 4px;
        padding-bottom: 8px;
        border-bottom: 2px solid #CBD5E1;
    }
    .section-sub {
        font-size: 0.92rem;
        color: #334155 !important;
        margin-bottom: 22px;
        font-weight: 500;
    }

    /* ── Data-source Badge ────────────────────────────────────────────── */
    .badge-demo {
        display: inline-block;
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
        border-radius: 6px;
        padding: 3px 12px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-left: 8px;
    }
    .badge-real {
        display: inline-block;
        background: #CCFBF1;
        color: #0F766E;
        border: 1px solid #5EEAD4;
        border-radius: 6px;
        padding: 3px 12px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-left: 8px;
    }

    /* ── Stat Rows in Analysis & Overview Page ────────────────────────── */
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 16px;
        border: 1px solid #E2E8F0;
        align-items: center;
        background: #FFFFFF !important;
        border-radius: 8px;
        margin-bottom: 6px;
        box-shadow: 0 1px 3px rgba(23, 36, 58, 0.04);
    }
    .stat-name  { font-weight: 600; color: #17243A !important; font-size: 0.95rem; }
    .stat-value { font-weight: 800; color: #17243A !important; font-size: 1.05rem; }
    .stat-note  { font-size: 0.82rem; color: #334155 !important; margin-top: 3px; font-weight: 500; }

    /* ── Plain-English Automatic Interpretation Box (#F1F5F9) ─────────── */
    .interpretation-card {
        background-color: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
        border-left: 6px solid #14B8A6 !important;
        border-radius: 12px !important;
        padding: 24px 28px !important;
        margin: 18px 0 !important;
        line-height: 1.75 !important;
        color: #334155 !important;
        box-shadow: 0 2px 10px rgba(23, 36, 58, 0.06) !important;
        box-sizing: border-box !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
    }
    .interpretation-card h4 {
        color: #17243A !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        margin-top: 20px !important;
        margin-bottom: 8px !important;
        line-height: 1.4 !important;
    }
    .interpretation-card h4:first-child {
        margin-top: 0 !important;
    }
    .interpretation-card p {
        color: #334155 !important;
        font-size: 0.98rem !important;
        line-height: 1.75 !important;
        margin-bottom: 16px !important;
        margin-top: 0 !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
    }
    .interpretation-card p:last-child {
        margin-bottom: 0 !important;
    }
    .interpretation-card strong {
        color: #17243A !important;
        font-weight: 700 !important;
    }
    .interpretation-card span {
        color: #334155 !important;
    }

    /* ── Export & Download Buttons (Navy #17243A with White Text) ─────── */
    [data-testid="stDownloadButton"] button,
    div.stDownloadButton > button,
    div.stDownloadButton button,
    div.stDownloadButton > button:link,
    div.stDownloadButton > button:visited,
    button[data-testid="baseButton-secondary"],
    button[data-testid="stBaseButton-secondary"] {
        background-color: #17243A !important;
        color: #FFFFFF !important;
        border: 1px solid #17243A !important;
        border-radius: 8px !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 2px 6px rgba(23, 36, 58, 0.15) !important;
    }
    [data-testid="stDownloadButton"] button:hover,
    div.stDownloadButton > button:hover,
    div.stDownloadButton button:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover {
        background-color: #2F80ED !important;
        color: #FFFFFF !important;
        border-color: #2F80ED !important;
        box-shadow: 0 4px 12px rgba(47, 128, 237, 0.28) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stDownloadButton"] button:active,
    div.stDownloadButton > button:active,
    div.stDownloadButton button:active,
    button[data-testid="baseButton-secondary"]:active,
    button[data-testid="stBaseButton-secondary"]:active {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        transform: translateY(0) !important;
    }
    [data-testid="stDownloadButton"] button:focus,
    div.stDownloadButton > button:focus,
    div.stDownloadButton button:focus,
    button[data-testid="baseButton-secondary"]:focus,
    button[data-testid="stBaseButton-secondary"]:focus {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(47, 128, 237, 0.35) !important;
        color: #FFFFFF !important;
    }
    /* Ensure label text inside download buttons is always bright white in all states */
    [data-testid="stDownloadButton"] button *,
    [data-testid="stDownloadButton"] button p,
    [data-testid="stDownloadButton"] button span,
    [data-testid="stDownloadButton"] button div,
    div.stDownloadButton button *,
    div.stDownloadButton button p,
    div.stDownloadButton button span,
    div.stDownloadButton > button *,
    div.stDownloadButton > button p,
    div.stDownloadButton > button span,
    button[data-testid="baseButton-secondary"] *,
    button[data-testid="stBaseButton-secondary"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stDownloadButton"] button:hover *,
    [data-testid="stDownloadButton"] button:hover p,
    [data-testid="stDownloadButton"] button:hover span,
    div.stDownloadButton button:hover *,
    div.stDownloadButton > button:hover * {
        color: #FFFFFF !important;
    }

    /* ── Primary Action Buttons (Blue #2F80ED) ────────────────────────── */
    button[data-testid="baseButton-primary"],
    button[data-testid="stBaseButton-primary"],
    .stButton > button[kind="primary"] {
        background-color: #2F80ED !important;
        color: #FFFFFF !important;
        border: 1px solid #2F80ED !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    button[data-testid="baseButton-primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #1E6AD1 !important;
        border-color: #1E6AD1 !important;
    }
    button[data-testid="baseButton-primary"] *,
    button[data-testid="stBaseButton-primary"] * {
        color: #FFFFFF !important;
    }

    /* ── Independent Chart Card Containers (st.container border=True) ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 14px 14px 10px 14px !important;
        box-shadow: 0 2px 8px rgba(23, 36, 58, 0.04) !important;
        margin-bottom: 16px !important;
    }

    /* Plotly chart container: stable, clean, no conflicting padding or transforms */
    [data-testid="stPlotlyChart"], .stPlotlyChart {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 0 !important;
        margin: 0 0 6px 0 !important;
        box-shadow: 0 1px 4px rgba(23, 36, 58, 0.03) !important;
        width: 100% !important;
    }

    /* When inside an independent card container, avoid nested borders */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"],
    [data-testid="stVerticalBlockBorderWrapper"] .stPlotlyChart {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Captions inside chart containers have clean spacing and high contrast */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {
        padding-top: 8px !important;
        border-top: 1px solid #F1F5F9 !important;
        margin-top: 4px !important;
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

# ── 6a. Theme Palette (Navy, Blue, Teal, White, Light BG) ────────────────────
C_NAVY        = "#17243A"   # Dark Navy -- chart titles, axis titles, primary text
C_DARK_GREY   = "#334155"   # Slate Grey -- tick labels, data labels, annotations
C_WHITE       = "#FFFFFF"   # Pure White -- cards, chart & plot backgrounds
C_LIGHT_BG    = "#F4F7FB"   # Very light blue-grey -- dashboard background
C_BEFORE      = "#2F80ED"   # Blue -- Before Practice
C_AFTER       = "#14B8A6"   # Teal -- After Practice
C_POS         = "#14B8A6"   # Teal -- positive improvement
C_NEG         = "#E11D48"   # Red/Crimson -- negative change (got slower)
C_GRID        = "#E2E8F0"   # Light subtle grey gridlines
C_BORDER      = "#CBD5E1"   # Clean axis lines and borders
C_TEXT        = "#17243A"   # High-contrast Navy text for headings
C_MUTED       = "#475569"   # Muted high-contrast slate

CHART_HEIGHT  = 420         # Fixed, stable height to prevent vertical layout shifts, overlapping, and page jumping

# Shared Plotly layout defaults applied to every chart
CHART_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", color=C_DARK_GREY, size=11),
    plot_bgcolor=C_WHITE,
    paper_bgcolor=C_WHITE,
    height=CHART_HEIGHT,
    margin=dict(l=55, r=25, t=60, b=50),
    hoverlabel=dict(
        bgcolor=C_NAVY,
        font_size=12,
        font_family="Inter, sans-serif",
        font_color="#FFFFFF",
        bordercolor=C_NAVY,
    ),
)


def format_p_value(pval: float | None) -> str:
    """
    Format a p-value with scientific precision and readable threshold.
    Avoids misleading 'p = 0.0000' for extremely small p-values.
    """
    if pval is None:
        return "N/A"
    if pval < 0.0001:
        return f"{pval:.4e} (p < 0.001)"
    return f"{pval:.4f}"


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
    color_class = {"blue": "blue", "teal": "teal", "navy": "navy", "green": "teal", "amber": "teal"}.get(color, "navy")
    return f"""
    <div class="kpi-card {color_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
    </div>
    """


def apply_chart_defaults(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply consistent layout defaults to any Plotly figure with high contrast and clean light theme."""
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=14, color=C_NAVY, family="Inter, sans-serif"),
            x=0.01,
            xanchor="left",
            y=0.96,
        ),
        legend=dict(
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor=C_GRID,
            borderwidth=1,
            font=dict(size=11, color=C_DARK_GREY, family="Inter, sans-serif"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    fig.update_xaxes(
        gridcolor=C_GRID,
        gridwidth=1,
        linecolor=C_BORDER,
        linewidth=1.2,
        zeroline=False,
        tickfont=dict(size=11, color=C_DARK_GREY, family="Inter, sans-serif"),
        title_font=dict(size=12, color=C_NAVY, family="Inter, sans-serif"),
    )
    fig.update_yaxes(
        gridcolor=C_GRID,
        gridwidth=1,
        linecolor=C_BORDER,
        linewidth=1.2,
        zeroline=False,
        tickfont=dict(size=11, color=C_DARK_GREY, family="Inter, sans-serif"),
        title_font=dict(size=12, color=C_NAVY, family="Inter, sans-serif"),
    )
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
            kpi_card("Students Tested", str(results["n"]), " pairs", "navy"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card("Mean Speed -- Before", f"{results['mean_before']:.1f}", " WPM", "blue"),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            kpi_card("Mean Speed -- After", f"{results['mean_after']:.1f}", " WPM", "teal"),
            unsafe_allow_html=True,
        )
    with c4:
        sign = "+" if results["mean_diff"] >= 0 else ""
        st.markdown(
            kpi_card("Mean Improvement", f"{sign}{results['mean_diff']:.1f}", " WPM", "teal"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Overview chart: grouped before/after bar ───────────────────────────────
    # This gives an at-a-glance view of every student's progress.
    # Each student gets two bars (before = blue #2F80ED, after = teal #14B8A6).
    left, right = st.columns([2, 1])

    with left:
        ids   = results["ids"]
        labels = [f"{sid}" for sid in ids]  # short labels for x-axis

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name="Before Practice",
            x=labels,
            y=results["before"].tolist(),
            marker_color=C_BEFORE,
            text=[f"{v:.0f}" for v in results["before"]],
            textposition="outside",
            textfont=dict(color=C_DARK_GREY, size=11, family="Inter, sans-serif"),
            hovertemplate="<b>%{x}</b><br>Before Practice: %{y:.1f} WPM<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="After Practice",
            x=labels,
            y=results["after"].tolist(),
            marker_color=C_AFTER,
            text=[f"{v:.0f}" for v in results["after"]],
            textposition="outside",
            textfont=dict(color=C_DARK_GREY, size=11, family="Inter, sans-serif"),
            hovertemplate="<b>%{x}</b><br>After Practice: %{y:.1f} WPM<extra></extra>",
        ))

        fig.update_layout(
            barmode="group",
            yaxis_title="Typing Speed (WPM)",
            xaxis_title="Student ID",
        )
        apply_chart_defaults(fig, "Before vs After Typing Speed -- All Students")
        st.plotly_chart(fig, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": False})

    with right:
        # Significance result card
        pval  = results["p_value"]
        sig   = results["significant"]
        alpha = results["alpha"]

        if pval is not None:
            p_str = format_p_value(pval)
            verdict = "<span style='color:#0F766E;font-weight:800;'>Significant Improvement ✅</span>" if sig else "<span style='color:#BE123C;font-weight:800;'>Not Statistically Significant ❌</span>"
            card_bg = "#CCFBF1" if sig else "#FFE4E6"
            border_col = "#14B8A6" if sig else "#E11D48"
        else:
            p_str   = "N/A"
            verdict = "<span style='color:#475569;font-weight:700;'>Cannot compute (zero variance)</span>"
            card_bg = "#F1F5F9"
            border_col = "#94A3B8"

        outcome_html = (
            f'<div style="background:{card_bg};border:1px solid #CBD5E1;border-left:5px solid {border_col};'
            f'border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(23,36,58,0.06);margin-top:6px;">'
            f'<div style="font-size:0.78rem;font-weight:800;color:#17243A;'
            f'text-transform:uppercase;letter-spacing:0.08em;">Hypothesis Test Outcome</div>'
            f'<div style="font-size:1.15rem;margin:10px 0 12px 0;">{verdict}</div>'
            f'<div style="font-size:0.9rem;color:#17243A;line-height:1.8;font-weight:500;">'
            f'<strong>p-value:</strong> {p_str}<br>'
            f'<strong>Significance level (&alpha;):</strong> {alpha}<br>'
            f'<strong>Degrees of freedom (df):</strong> {results["df"]}'
            f'</div></div>'
        )
        st.markdown(outcome_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Quick stats mini-table with high contrast
        st.markdown("<h4 style='color:#17243A;margin-top:8px;margin-bottom:8px;'>⚡ Quick Stats</h4>", unsafe_allow_html=True)
        quick = {
            "Mean difference (d_bar)": f"{results['mean_diff']:+.2f} WPM",
            "SD of differences (s_d)": f"{results['std_diff']:.2f}",
            "Standard Error (SE_d)":   f"{results['standard_error']:.2f} WPM",
            "95% Confidence Interval": f"[{results['ci_95_lower']:.2f}, {results['ci_95_upper']:.2f}]",
            "t-statistic":             f"{results['t_statistic']:.4f}" if results["t_statistic"] is not None else "N/A",
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

        styler = df.style.format({
            "Before (WPM)": "{:.1f}",
            "After (WPM)":  "{:.1f}",
            "Change (WPM)": "{:+.1f}",
        })
        styler_method = getattr(styler, "map", getattr(styler, "applymap", None))
        styled_df = styler_method(
            lambda v: "color: #0F766E; font-weight: 700"
            if isinstance(v, (int, float)) and v > 0
            else ("color: #E11D48; font-weight: 700"
                  if isinstance(v, (int, float)) and v < 0
                  else ""),
            subset=["Change (WPM)"],
        ) if styler_method else styler

        st.dataframe(
            styled_df,
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

    # ── Row 1: Charts 1 & 2 (top row) ─────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            # --- Chart 1: Grouped Bar -- individual student before vs after ---
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                name="Before Practice",
                x=ids,
                y=before.tolist(),
                marker_color=C_BEFORE,
                text=[f"{v:.0f}" for v in results["before"]],
                textposition="outside",
                textfont=dict(color=C_DARK_GREY, size=11, family="Inter, sans-serif"),
                hovertemplate="<b>%{x}</b><br>Before Practice: %{y:.1f} WPM<extra></extra>",
            ))
            fig1.add_trace(go.Bar(
                name="After Practice",
                x=ids,
                y=after.tolist(),
                marker_color=C_AFTER,
                text=[f"{v:.0f}" for v in results["after"]],
                textposition="outside",
                textfont=dict(color=C_DARK_GREY, size=11, family="Inter, sans-serif"),
                hovertemplate="<b>%{x}</b><br>After Practice: %{y:.1f} WPM<extra></extra>",
            ))
            fig1.update_layout(
                barmode="group",
                yaxis_title="Typing Speed (WPM)",
                xaxis_title="Student ID",
            )
            apply_chart_defaults(fig1, "Before & After Typing Speed per Student")
            st.plotly_chart(
                fig1,
                use_container_width=True,
                theme=None,
                key="chart_grouped_bar",
                config={"responsive": True, "displayModeBar": False},
            )
            st.caption(
                "Each student has two bars. Blue (#2F80ED) = speed before practice, "
                "Teal (#14B8A6) = speed after practice."
            )

    with col2:
        with st.container(border=True):
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
                line=dict(color="#64748B", width=1.8, dash="dash"),
            )
            fig2.add_annotation(
                x=axis_max - 2, y=axis_max - 4,
                text="No change (y = x)",
                showarrow=False,
                font=dict(size=11, color=C_DARK_GREY, family="Inter, sans-serif"),
            )

            fig2.add_trace(go.Scatter(
                x=before.tolist(),
                y=after.tolist(),
                mode="markers+text",
                text=ids,
                textposition="top center",
                textfont=dict(size=11, color=C_DARK_GREY, family="Inter, sans-serif"),
                marker=dict(
                    color=[C_POS if d >= 0 else C_NEG for d in diffs],
                    size=12,
                    line=dict(color="#FFFFFF", width=1.8),
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
                xaxis=dict(title="Before Practice (WPM)", range=[axis_min, axis_max]),
                yaxis=dict(title="After Practice (WPM)",  range=[axis_min, axis_max]),
                showlegend=False,
            )
            apply_chart_defaults(fig2, "Before vs After (per Student) -- Scatter Plot")
            st.plotly_chart(
                fig2,
                use_container_width=True,
                theme=None,
                key="chart_scatter",
                config={"responsive": True, "displayModeBar": False},
            )
            st.caption(
                "Points above the dashed line improved; below the line means slower after practice. "
                "Teal (#14B8A6) = improved, Red (#E11D48) = declined."
            )

    # ── Row 2: Charts 3 & 4 (bottom row) ──────────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            # --- Chart 3: Improvement bar -- (after - before) per student ---
            bar_colors = [C_POS if d >= 0 else C_NEG for d in diffs]

            fig3 = go.Figure(go.Bar(
                x=ids,
                y=diffs.tolist(),
                marker_color=bar_colors,
                text=[f"{d:+.1f}" for d in diffs],
                textposition="outside",
                textfont=dict(color=C_DARK_GREY, size=11, family="Inter, sans-serif"),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Improvement: %{y:+.1f} WPM<extra></extra>"
                ),
            ))

            # Horizontal zero baseline
            fig3.add_hline(y=0, line_color="#94A3B8", line_width=1.5)

            # Dashed mean difference reference line
            fig3.add_hline(
                y=float(results["mean_diff"]),
                line_dash="dash",
                line_color=C_NAVY,
                line_width=1.5,
                annotation_text=f"Mean d_bar = {results['mean_diff']:+.1f} WPM",
                annotation_position="top left",
                annotation_font=dict(color=C_NAVY, size=11, family="Inter, sans-serif"),
            )

            fig3.update_layout(
                yaxis_title="WPM Change (After - Before)",
                xaxis_title="Student ID",
            )
            apply_chart_defaults(fig3, "Individual WPM Improvement per Student")
            st.plotly_chart(
                fig3,
                use_container_width=True,
                theme=None,
                key="chart_improvement",
                config={"responsive": True, "displayModeBar": False},
            )
            st.caption(
                "Positive bars (Teal) = student typed faster after practice. "
                "Negative bars (Red) = student typed slower. Dashed line = mean change."
            )

    with col4:
        with st.container(border=True):
            # --- Chart 4: Box plots -- distribution of before & after speeds ---
            # A box plot shows the median (middle line), the interquartile range
            # (the box itself), and outliers (individual dots).
            fig4 = go.Figure()

            fig4.add_trace(go.Box(
                y=before.tolist(),
                name="Before Practice",
                marker_color=C_BEFORE,
                boxmean=True,           # Show mean as a dashed line inside the box
                hovertemplate="Before WPM<br>%{y:.1f}<extra></extra>",
            ))
            fig4.add_trace(go.Box(
                y=after.tolist(),
                name="After Practice",
                marker_color=C_AFTER,
                boxmean=True,
                hovertemplate="After WPM<br>%{y:.1f}<extra></extra>",
            ))

            fig4.update_layout(
                yaxis_title="Typing Speed (WPM)",
                showlegend=True,
            )
            apply_chart_defaults(fig4, "Speed Distribution -- Before vs After")
            st.plotly_chart(
                fig4,
                use_container_width=True,
                theme=None,
                key="chart_distribution",
                config={"responsive": True, "displayModeBar": False},
            )
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
        st.markdown("<h4 style='color:#17243A;'>📐 Descriptive Statistics</h4>", unsafe_allow_html=True)
        st.markdown(
            "<span style='color:#334155;'>Summary of raw typing speeds before and after deliberate practice.</span>",
            unsafe_allow_html=True,
        )

        stats_rows = [
            ("Sample Size (n paired students)",
             str(results["n"]),
             "Number of matched before/after student observations."),
            ("Mean Speed -- Before (x_bar1)",
             f"{results['mean_before']:.4f} WPM",
             "Average typing speed before the practice session."),
            ("Mean Speed -- After (x_bar2)",
             f"{results['mean_after']:.4f} WPM",
             "Average typing speed after the practice session."),
            ("Sample Standard Deviation -- Before (s1)",
             f"{results['std_before']:.4f}",
             "Spread of pre-practice speeds (Bessel's correction n-1)."),
            ("Sample Standard Deviation -- After (s2)",
             f"{results['std_after']:.4f}",
             "Spread of post-practice speeds (Bessel's correction n-1)."),
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
        st.markdown("<h4 style='color:#17243A;'>🔁 Paired Difference Statistics</h4>", unsafe_allow_html=True)
        st.markdown(
            "<span style='color:#334155;'>Computed on individual differences: <strong>d = after - before</strong>.</span>",
            unsafe_allow_html=True,
        )

        ci_str = f"[{results['ci_95_lower']:.4f}, {results['ci_95_upper']:.4f}] WPM" if results.get("ci_95_lower") is not None else "N/A"
        t_crit_str = f"{results['t_crit']:.4f}" if results.get("t_crit") is not None else "N/A"

        diffs_rows = [
            ("Mean Difference (d_bar)",
             f"{results['mean_diff']:+.4f} WPM",
             "Average improvement per student. Positive = speed gained."),
            ("Sample SD of Differences (s_d)",
             f"{results['std_diff']:.4f}",
             "Standard deviation of the improvements across students."),
            ("Standard Error (SE_d = s_d / sqrt(n))",
             f"{results['standard_error']:.4f} WPM",
             "Uncertainty in estimated d_bar. Decreases as sample size grows."),
            ("Critical Value (t* at alpha=0.05)",
             t_crit_str,
             f"Two-tailed critical t-value with df = {results['df']}."),
            ("95% Confidence Interval",
             ci_str,
             "Estimated range for the true population mean improvement."),
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

    # ── Row 2: Paired t-test results + 95% Confidence Interval Card ──────────
    col_test, col_explain = st.columns([1.1, 1.3])

    with col_test:
        st.markdown("<h4 style='color:#17243A;'>🧪 Paired-Sample t-Test Results</h4>", unsafe_allow_html=True)
        st.markdown(
            "<span style='color:#334155;'>Inferential test to evaluate whether observed improvement is statistically significant.</span>",
            unsafe_allow_html=True,
        )

        t_val = results["t_statistic"]
        p_val = results["p_value"]
        alpha = results["alpha"]
        sig   = results["significant"]

        ttest_rows = [
            ("Null Hypothesis (H0)",
             "mu_d = 0",
             "Practice produces no net change in typing speed."),
            ("Alternative Hypothesis (H1)",
             "mu_d != 0",
             "Practice changes typing speed (two-tailed test)."),
            ("Significance Threshold (alpha)",
             str(alpha),
             "We accept a 5% maximum risk of Type I error."),
            ("Degrees of Freedom (df)",
             str(results["df"]),
             "df = n - 1."),
            ("Paired t-Statistic",
             f"{t_val:.4f}" if t_val is not None else "N/A",
             "t = d_bar / SE_d. Distance from zero in SE units."),
            ("Calculated p-Value",
             format_p_value(p_val),
             "Probability of observing this result under H0."),
            ("Statistical Decision",
             "Reject H0 ✅ (Significant)" if sig else "Fail to Reject H0 ❌",
             f"p {'<' if sig else '>='} alpha = {alpha}"),
        ]

        for name, value, note in ttest_rows:
            val_style = "color:#17243A;font-weight:800"
            if name == "Statistical Decision":
                val_style = "color:#0F766E;font-weight:800" if sig else "color:#E11D48;font-weight:800"
            st.markdown(
                f"""
                <div class="stat-row">
                    <div>
                        <div class="stat-name">{name}</div>
                        <div class="stat-note">{note}</div>
                    </div>
                    <div class="stat-value" style="{val_style}">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_explain:
        st.markdown("<h4 style='color:#17243A;'>🎯 Confidence Interval & Interpretation</h4>", unsafe_allow_html=True)

        if results.get("ci_95_lower") is not None and results.get("ci_95_upper") is not None:
            moe = results["ci_95_upper"] - results["mean_diff"]
            ci_card_html = (
                f'<div style="background-color:#F1F5F9;border:1px solid #CBD5E1;border-left:5px solid #2F80ED;'
                f'border-radius:10px;padding:18px 22px;margin-bottom:16px;box-shadow:0 2px 6px rgba(23,36,58,0.05);">'
                f'<div style="font-size:0.8rem;font-weight:800;color:#17243A;text-transform:uppercase;letter-spacing:0.07em;">'
                f'95% Confidence Interval for Mean Improvement</div>'
                f'<div style="font-size:1.45rem;font-weight:800;color:#2F80ED;margin:8px 0 6px 0;">'
                f'[{results["ci_95_lower"]:.2f}, {results["ci_95_upper"]:.2f}] WPM</div>'
                f'<div style="font-size:0.9rem;color:#334155;line-height:1.6;">'
                f'Margin of error: &plusmn;{moe:.2f} WPM.<br>'
                f'We are 95% confident that the true average improvement across all comparable students is between '
                f'<strong style="color:#17243A;">{results["ci_95_lower"]:.2f}</strong> and '
                f'<strong style="color:#17243A;">{results["ci_95_upper"]:.2f} WPM</strong>.</div>'
                f'</div>'
            )
            st.markdown(ci_card_html, unsafe_allow_html=True)

        exp_html = (
            f'<div style="line-height:1.7;font-size:0.92rem;">'
            f'<p style="color:#334155;margin:0 0 10px 0;"><strong style="color:#17243A;">Why is a paired t-test required?</strong><br>'
            f'Because measurements are taken on the exact same students before and after practice. A paired test analyzes the intra-subject differences (d = after - before), isolating the effect of practice from natural baseline typing ability.</p>'
            f'<p style="color:#334155;margin:0 0 10px 0;"><strong style="color:#17243A;">How to interpret the p-value:</strong><br>'
            f'The p-value is the probability of observing an improvement at least as large as what we measured purely by chance if practice had no true effect. A p-value below 0.05 provides strong evidence to reject the null hypothesis.</p>'
            f'</div>'
        )
        st.markdown(exp_html, unsafe_allow_html=True)

        # Show the student-level differences as a mini chart with high contrast
        diffs = results["differences"]
        ids   = results["ids"]

        fig_mini = go.Figure(go.Bar(
            x=ids,
            y=diffs.tolist(),
            marker_color=[C_POS if d >= 0 else C_NEG for d in diffs],
            text=[f"{d:+.1f}" for d in diffs],
            textposition="outside",
            textfont=dict(color=C_DARK_GREY, size=10, family="Inter, sans-serif"),
            hovertemplate="<b>%{x}</b><br>Difference (d): %{y:+.1f} WPM<extra></extra>",
        ))
        fig_mini.add_hline(
            y=float(results["mean_diff"]),
            line_dash="dash",
            line_color=C_NAVY,
            line_width=1.8,
            annotation_text=f"Mean d_bar = {results['mean_diff']:+.2f}",
            annotation_position="top left",
            annotation_font=dict(color=C_NAVY, size=11, family="Inter, sans-serif"),
        )
        fig_mini.update_layout(
            height=210,
            margin=dict(l=30, r=10, t=30, b=30),
            yaxis_title="Change (WPM)",
            showlegend=False,
            **{k: v for k, v in CHART_LAYOUT.items() if k not in ("margin",)},
        )
        st.plotly_chart(fig_mini, use_container_width=True, theme=None, config={"responsive": True, "displayModeBar": False})
        st.caption("Individual differences (d = after - before). Dashed line = mean difference d_bar.")


# =============================================================================
# SECTION 11 -- PAGE: CONCLUSION & EXPORT
# =============================================================================

def generate_automatic_interpretation(results: dict, data_source: str) -> dict:
    """
    Generate a dynamic, academically rigorous, plain-English summary of the study
    using pure Python logic on the actual calculated statistics.
    No generative AI API call is used.
    """
    n          = results["n"]
    mean_b     = results["mean_before"]
    mean_a     = results["mean_after"]
    mean_d     = results["mean_diff"]
    std_b      = results["std_before"]
    std_a      = results["std_after"]
    std_d      = results["std_diff"]
    se_d       = results.get("standard_error", std_d / (n ** 0.5) if n > 0 else 0.0)
    ci_low     = results.get("ci_95_lower")
    ci_high    = results.get("ci_95_upper")
    t_val      = results["t_statistic"]
    df         = results["df"]
    p_val      = results["p_value"]
    sig        = results["significant"]
    alpha      = results["alpha"]

    abs_d = abs(mean_d)
    direction_verb = "increased" if mean_d > 0 else ("decreased" if mean_d < 0 else "remained identical")
    direction_adj  = "faster" if mean_d > 0 else ("slower" if mean_d < 0 else "unchanged")
    pct_change     = (mean_d / mean_b * 100.0) if mean_b > 0 else 0.0

    # 1. Change in typing speed
    change_text = (
        f"Across the cohort of {n} paired students, average typing speed {direction_verb} "
        f"from {mean_b:.2f} WPM (sample SD = {std_b:.2f}) before practice to "
        f"{mean_a:.2f} WPM (sample SD = {std_a:.2f}) after practice. "
        f"The mean paired change was {mean_d:+.2f} WPM (a {pct_change:+.1f}% change), "
        f"meaning students typed on average {abs_d:.2f} WPM {direction_adj} after the practice session. "
        f"The sample standard deviation of differences was s_d = {std_d:.2f} WPM, with a standard error of SE_d = {se_d:.2f} WPM."
    )

    # 2. Statistical significance at alpha = 0.05
    if p_val is not None:
        p_str = format_p_value(p_val)
        if sig:
            sig_text = (
                f"The difference is statistically significant at the alpha = {alpha} significance level (two-tailed p = {p_str} < {alpha}). "
                f"Because the calculated p-value is less than the predetermined 0.05 threshold, the observed gain cannot be attributed to chance."
            )
        else:
            sig_text = (
                f"The difference is NOT statistically significant at the alpha = {alpha} level (two-tailed p = {p_str} >= {alpha}). "
                f"There is insufficient evidence in this dataset to confirm that deliberate practice caused a reliable shift in speed."
            )
    else:
        sig_text = "The paired t-test could not be evaluated due to zero variance across student differences."

    # 3. Meaning of the p-value
    if p_val is not None:
        if p_val < 0.001:
            p_meaning = (
                f"The calculated p-value ({p_str}) measures the probability of observing a speed improvement "
                f"of {abs_d:.2f} WPM or greater purely by random fluctuation if deliberate practice had no genuine effect. "
                f"Because this probability is virtually zero (less than 1 in 1,000), it provides overwhelming empirical evidence "
                f"that deliberate keyboard practice directly improved student typing proficiency."
            )
        elif p_val < 0.05:
            p_meaning = (
                f"The p-value of {p_str} indicates there is approximately a {p_val*100:.1f}% likelihood of observing an average gain of "
                f"{abs_d:.2f} WPM by chance if practice had zero true effect. Because this falls below the 5% risk threshold, "
                f"we conclude that deliberate practice had a genuine positive effect."
            )
        else:
            p_meaning = (
                f"The p-value of {p_str} indicates there is a {p_val*100:.1f}% likelihood that a difference of this size could arise "
                f"purely from random sampling variability. Because this is higher than 5%, we cannot rule out random chance."
            )
    else:
        p_meaning = "p-value is undefined when all paired differences are identical."

    # 4. Null hypothesis evaluation
    if sig:
        h0_text = (
            f"The empirical data supports REJECTING the null hypothesis (H0: mu_d = 0). "
            f"We accept the alternative hypothesis (H1: mu_d != 0), confirming that the practice regimen produced "
            f"a statistically verifiable effect on student keyboarding skills."
        )
    else:
        h0_text = (
            f"The data FAILS TO REJECT the null hypothesis (H0: mu_d = 0). "
            f"We retain H0 as there is inadequate statistical evidence to demonstrate a non-zero effect at the 5% level."
        )

    # 5. 95% Confidence Interval interpretation
    if ci_low is not None and ci_high is not None:
        ci_text = (
            f"The 95% confidence interval for the population mean improvement is [{ci_low:.2f}, {ci_high:.2f}] WPM. "
            f"We are 95% confident that the true average improvement for the broader population of similar students "
            f"lies within this range. Because the lower bound ({ci_low:.2f} WPM) is strictly greater than 0, "
            f"it affirms that the true population impact is positive."
        )
    else:
        ci_text = "Confidence interval not available."

    return {
        "change_text": change_text,
        "sig_text": sig_text,
        "p_meaning": p_meaning,
        "h0_text": h0_text,
        "ci_text": ci_text,
        "sig": sig,
    }


def page_conclusion_export():
    """
    Conclusion & Export page: auto-generated plain-language summary + downloads.

    AUTO-GENERATED CONCLUSION
    -------------------------
    The conclusion is dynamically generated using Python logic from the calculated
    statistics -- it updates automatically whenever data changes without relying
    on hardcoded templates or external LLM APIs.
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
    ci_low     = results.get("ci_95_lower")
    ci_high    = results.get("ci_95_upper")
    data_label = "sample" if st.session_state.data_source == "demo" else "collected"

    # Generate the dynamic interpretation
    interp = generate_automatic_interpretation(results, st.session_state.data_source)

    # ── Key numbers at a glance ────────────────────────────────────────────────
    st.markdown("<h4 style='color:#17243A;margin-bottom:12px;'>⚡ Key Numbers at a Glance</h4>", unsafe_allow_html=True)

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.markdown(kpi_card("Mean Before", f"{mean_b:.1f}", " WPM", "blue"), unsafe_allow_html=True)
    with col_b:
        st.markdown(kpi_card("Mean After", f"{mean_a:.1f}", " WPM", "teal"), unsafe_allow_html=True)
    with col_c:
        sign = "+" if mean_d >= 0 else ""
        st.markdown(kpi_card("Mean Difference", f"{sign}{mean_d:.1f}", " WPM", "teal"), unsafe_allow_html=True)
    with col_d:
        p_card_str = format_p_value(p_val)
        st.markdown(kpi_card("p-Value", p_card_str, "", "navy"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Automatic Plain-English Interpretation Section ────────────────────────
    st.markdown("<h3 style='color:#17243A;'>🤖 Automatic Result Interpretation</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#334155;'>Generated automatically from your verified dataset using inferential statistical logic:</p>",
        unsafe_allow_html=True,
    )

    border_accent = "#14B8A6" if sig else "#E11D48"
    interpretation_html = (
        f'<div class="interpretation-card" style="background-color:#F1F5F9;border:1px solid #CBD5E1;'
        f'border-left:6px solid {border_accent};border-radius:12px;padding:24px 28px;margin:18px 0;'
        f'box-shadow:0 2px 10px rgba(23,36,58,0.06);color:#334155;box-sizing:border-box;width:100%;'
        f'overflow-wrap:break-word;word-break:normal;">'
        f'<h4 style="color:#17243A;font-size:1.15rem;font-weight:800;margin:0 0 8px 0;line-height:1.4;">'
        f'📈 1. Average Typing Speed Change</h4>'
        f'<p style="color:#334155;font-size:0.98rem;line-height:1.75;margin:0 0 18px 0;">'
        f'{interp["change_text"]}</p>'
        f'<h4 style="color:#17243A;font-size:1.15rem;font-weight:800;margin:0 0 8px 0;line-height:1.4;">'
        f'⚖️ 2. Statistical Significance</h4>'
        f'<p style="color:#334155;font-size:0.98rem;line-height:1.75;margin:0 0 18px 0;">'
        f'{interp["sig_text"]}</p>'
        f'<h4 style="color:#17243A;font-size:1.15rem;font-weight:800;margin:0 0 8px 0;line-height:1.4;">'
        f'🎲 3. What the P-value Means</h4>'
        f'<p style="color:#334155;font-size:0.98rem;line-height:1.75;margin:0 0 18px 0;">'
        f'{interp["p_meaning"]}</p>'
        f'<h4 style="color:#17243A;font-size:1.15rem;font-weight:800;margin:0 0 8px 0;line-height:1.4;">'
        f'🛡️ 4. Null Hypothesis Decision</h4>'
        f'<p style="color:#334155;font-size:0.98rem;line-height:1.75;margin:0 0 18px 0;">'
        f'{interp["h0_text"]}</p>'
        f'<h4 style="color:#17243A;font-size:1.15rem;font-weight:800;margin:0 0 8px 0;line-height:1.4;">'
        f'🎯 5. 95% Confidence Interval</h4>'
        f'<p style="color:#334155;font-size:0.98rem;line-height:1.75;margin:0;">'
        f'{interp["ci_text"]}</p>'
        f'</div>'
    )
    st.markdown(interpretation_html, unsafe_allow_html=True)

    # ── Export: full data CSV & Summary TXT ─────────────────────────────────────
    st.markdown("---")
    st.markdown("<h3 style='color:#17243A;'>⬇ Export Results</h3>", unsafe_allow_html=True)

    # Build the export DataFrame
    export_df = records_to_df().copy()
    export_df["Significant"]  = sig
    export_df["p-value"]      = format_p_value(p_val)
    export_df["t-statistic"]  = f"{t_val:.4f}" if t_val is not None else "N/A"
    export_df["df"]           = df
    export_df["95% CI Lower"] = f"{ci_low:.4f}" if ci_low is not None else "N/A"
    export_df["95% CI Upper"] = f"{ci_high:.4f}" if ci_high is not None else "N/A"
    export_df["alpha"]        = alpha
    export_df["Data Source"]  = data_label

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.download_button(
            label="📥 Download Full Results (CSV)",
            data=csv_bytes,
            file_name="typing_speed_results.csv",
            mime="text/csv",
            help="Downloads the student data with per-student differences, 95% CI, and t-test summary.",
        )

    with col_e2:
        # Build plain-text summary for academic submission
        ci_summary_str = f"[{ci_low:.4f}, {ci_high:.4f}] WPM" if ci_low is not None else "N/A"
        summary_text = (
            "TYPING SPEED ANALYSIS -- MDM MINI PROJECT\n"
            "=" * 60 + "\n"
            f"Data source   : {data_label.title()}\n"
            f"Students (n)  : {n} paired observations\n"
            f"Significance  : alpha = {alpha}\n"
            "=" * 60 + "\n\n"
            "[1. DESCRIPTIVE STATISTICS]\n"
            "-" * 35 + "\n"
            f"Mean Before   : {mean_b:.4f} WPM\n"
            f"Mean After    : {mean_a:.4f} WPM\n"
            f"SD Before     : {std_b:.4f}\n"
            f"SD After      : {std_a:.4f}\n\n"
            "[2. PAIRED DIFFERENCES (after - before)]\n"
            "-" * 35 + "\n"
            f"Mean diff (d_bar) : {mean_d:+.4f} WPM\n"
            f"SD of diffs (s_d) : {std_d:.4f}\n"
            f"Standard Error SE : {results.get('standard_error', 0.0):.4f} WPM\n"
            f"95% CI on Diff    : {ci_summary_str}\n\n"
            "[3. PAIRED t-TEST]\n"
            "-" * 35 + "\n"
            f"t-statistic   : {f'{t_val:.4f}' if t_val is not None else 'N/A'}\n"
            f"df            : {df}\n"
            f"p-value       : {format_p_value(p_val)}\n"
            f"Significant   : {'Yes (Reject H0)' if sig else 'No (Fail to Reject H0)'}\n\n"
            "[4. AUTOMATED PLAIN-ENGLISH INTERPRETATION]\n"
            "-" * 35 + "\n"
            f"* Speed Change: {interp['change_text']}\n\n"
            f"* Significance: {interp['sig_text']}\n\n"
            f"* p-Value Meaning: {interp['p_meaning']}\n\n"
            f"* Hypothesis Test: {interp['h0_text']}\n\n"
            f"* 95% Confidence Interval: {interp['ci_text']}\n"
        )

        st.download_button(
            label="📄 Download Summary Report (TXT)",
            data=summary_text.encode("utf-8"),
            file_name="typing_speed_summary.txt",
            mime="text/plain",
            help="Downloads an academically formatted text summary ready for submission.",
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
                '<div style="background:rgba(245,158,11,0.18);border:1px solid #F59E0B;border-radius:6px;padding:8px 10px;'
                'font-size:0.75rem;color:#FDE68A;margin-top:8px;line-height:1.5;">'
                "⚠ Using sample data.<br>Add your real data in<br><b>Student Data</b>."
                "</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown(
            '<div style="font-size:0.75rem;color:#94A3B8;line-height:1.6;">'
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
