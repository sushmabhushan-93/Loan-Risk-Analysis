import streamlit as st

st.set_page_config(
    page_title="Loan Risk Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global Styles ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f1923 0%, #162033 100%);
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { 
    font-size: 0.95rem !important; 
    padding: 6px 0;
}

/* Main bg */
.main { background: #f7f8fc; }

/* Page header */
.page-header {
    background: linear-gradient(135deg, #0f1923 0%, #1e3a5f 100%);
    color: white;
    padding: 2.5rem 2rem 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.page-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(99,179,237,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.page-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    margin: 0 0 0.4rem;
}
.page-header p { margin: 0; opacity: 0.75; font-size: 0.95rem; }

/* Metric cards */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 1px 8px rgba(0,0,0,0.07);
    border-left: 4px solid #3182ce;
}
.metric-card.green { border-left-color: #38a169; }
.metric-card.red   { border-left-color: #e53e3e; }
.metric-card.amber { border-left-color: #d69e2e; }
.metric-card h3 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: #718096; margin: 0 0 0.3rem; }
.metric-card .value { font-family: 'DM Serif Display', serif; font-size: 2rem; color: #1a202c; margin: 0; line-height: 1; }
.metric-card .sub { font-size: 0.8rem; color: #a0aec0; margin-top: 4px; }

/* Section titles */
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: #1a202c;
    margin: 1.8rem 0 1rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid #e2e8f0;
}

/* Risk badge */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-low  { background:#c6f6d5; color:#276749; }
.badge-high { background:#fed7d7; color:#9b2c2c; }

/* Prediction result box */
.pred-box {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.pred-box .risk-label {
    font-family: 'DM Serif Display', serif;
    font-size: 2.5rem;
}

/* Info callout */
.callout {
    background: #ebf8ff;
    border-left: 4px solid #3182ce;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #2c5282;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0 1.5rem;'>
        <div style='font-family:"DM Serif Display",serif; font-size:1.4rem; color:#63b3ed;'>🏦 LoanRisk IQ</div>
        <div style='font-size:0.75rem; color:#718096; margin-top:4px;'>Loan Risk Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["📊 EDA & Data Insights", "📈 Power BI Dashboards", "🤖 Predictive Model"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("<div style='font-size:0.75rem; color:#4a5568;'>Upload your customer data on the EDA page to get started.</div>", unsafe_allow_html=True)

# ── Page Router ──────────────────────────────────────────────────────────────
if page == "📊 EDA & Data Insights":
    from pages import eda
    eda.show()
elif page == "📈 Power BI Dashboards":
    from pages import powerbi
    powerbi.show()
elif page == "🤖 Predictive Model":
    from pages import model
    model.show()
