import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

C = {"P1": "#3182ce", "P2": "#38a169", "P3": "#d69e2e", "P4": "#e53e3e"}
BLUE = "#3182ce"; GREEN = "#38a169"; RED = "#e53e3e"; AMBER = "#d69e2e"; PURPLE = "#805ad5"

SENTINEL_COLS = ['CC_utilization','PL_utilization','time_since_recent_deliquency',
                 'max_delinquency_level','time_since_first_deliquency','max_unsec_exposure_inPct']

def clean(df):
    df = df.copy()
    df.replace(-99999, np.nan, inplace=True)
    df.drop(columns=[c for c in SENTINEL_COLS if c in df.columns], inplace=True, errors='ignore')
    for c in ['max_deliq_6mts','max_deliq_12mts']:
        if c in df.columns: df[c] = df[c].fillna(0)
    num = df.select_dtypes('number').columns
    df[num] = df[num].fillna(df[num].median())
    return df

def age_group(age):
    if age < 30:   return "21-29"
    elif age < 40: return "30-39"
    elif age < 50: return "40-49"
    elif age < 60: return "50-59"
    else:          return "60+"

def metric_card(label, value, color="#3182ce"):
    return f"""<div style='background:white;border-radius:12px;padding:1rem 1.2rem;
        box-shadow:0 1px 8px rgba(0,0,0,0.07);border-left:4px solid {color};'>
        <div style='font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#718096;margin-bottom:4px;'>{label}</div>
        <div style='font-size:1.9rem;color:#1a202c;line-height:1;font-weight:700;'>{value}</div>
    </div>"""

def col_find(df, candidates):
    return next((c for c in candidates if c in df.columns), None)

def show():
    st.markdown("""
    <div class='page-header'>
        <h1>📈 Loan Risk Dashboard</h1>
        <p>Interactive replica of your Power BI report — 3 pages covering Overview, Credit Risk, and Trade Lines.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Upload Dataset</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        f1 = st.file_uploader("External CIBIL Data (CSV/Excel)", type=["csv","xlsx"], key="db1")
    with c2:
        f2 = st.file_uploader("Internal Bank Data (optional)", type=["csv","xlsx"], key="db2")

    def read(f):
        return pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)

    if f1 is None:
        st.markdown("<div class='callout'>👆 Upload your dataset to populate all dashboard charts.</div>", unsafe_allow_html=True)
        _show_placeholders()
        return

    df = read(f1)
    if f2:
        df2 = read(f2)
        if "PROSPECTID" in df.columns and "PROSPECTID" in df2.columns:
            df = pd.merge(df, df2, on="PROSPECTID", how="inner")
    df = clean(df)

    if "Approved_Flag" not in df.columns:
        st.error("Column 'Approved_Flag' not found.")
        return

    df["High_Risk"] = df["Approved_Flag"].isin(["P3","P4"]).astype(int)

    age_col   = col_find(df, ["Age","AGE","age"])
    inc_col   = col_find(df, ["NETMONTHLYINCOME","Net_Monthly_Income","income"])
    score_col = col_find(df, ["Credit_Score","credit_score","CREDIT_SCORE"])
    edu_col   = col_find(df, ["EDUCATION","Education","education"])
    gen_col   = col_find(df, ["GENDER","Gender","gender"])
    mar_col   = col_find(df, ["MARITALSTATUS","Marital_Status"])
    deliq_col = col_find(df, ["Num_Deliq","num_deliquency","total_delinquency_count","max_deliq_6mts"])
    dpd_col   = col_find(df, ["num_std_12mts","Avg_30DPD","dpd_30plus","num_std"])
    mp_col    = col_find(df, ["num_missed_payments","Num_Missed_Payments","missed_payments"])
    act_tl    = col_find(df, ["Tot_Active_TL","tot_active_TL"])
    clo_tl    = col_find(df, ["Tot_Closed_TL","tot_closed_TL"])
    tot_tl    = col_find(df, ["Total_TL","total_TL","tot_TL"])
    old_tl    = col_find(df, ["Age_Oldest_TL","age_oldest_TL"])

    if age_col:
        df["Age_Group"] = df[age_col].apply(age_group)
    if mp_col:
        def band(x):
            if x == 0: return "0 - None"
            elif x <= 2: return "1 - 2"
            elif x <= 5: return "3 - 5"
            else: return "6+"
        df["Missed_pmt_band"] = df[mp_col].apply(band)

    # ── Filters ───────────────────────────────────────────────────────────
    with st.expander("🔽 Global Filters", expanded=False):
        fc = st.columns(3)
        f_flag = fc[0].selectbox("Approved Flag", ["All"] + sorted(df["Approved_Flag"].dropna().unique().tolist()))
        f_edu  = fc[1].selectbox("Education", ["All"] + (sorted(df[edu_col].dropna().unique().tolist()) if edu_col else []))
        f_gen  = fc[2].selectbox("Gender",    ["All"] + (sorted(df[gen_col].dropna().unique().tolist()) if gen_col else []))

    dff = df.copy()
    if f_flag != "All": dff = dff[dff["Approved_Flag"] == f_flag]
    if f_edu  != "All" and edu_col: dff = dff[dff[edu_col] == f_edu]
    if f_gen  != "All" and gen_col: dff = dff[dff[gen_col] == f_gen]

    high_pct = dff["High_Risk"].mean() * 100

    # ══════════════════════════════════════════════════════
    # PAGE 1 — Customer Overview
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📋 Page 1 — Customer Overview")

    cols = st.columns(4)
    cols[0].markdown(metric_card("Total Customers", f"{len(dff):,}", BLUE), unsafe_allow_html=True)
    cols[1].markdown(metric_card("Avg Credit Score", f"{dff[score_col].mean():.0f}" if score_col else "N/A", GREEN), unsafe_allow_html=True)
    cols[2].markdown(metric_card("Avg Monthly Income", f"₹{dff[inc_col].mean():,.0f}" if inc_col else "N/A", PURPLE), unsafe_allow_html=True)
    cols[3].markdown(metric_card("High Risk %", f"{high_pct:.1f}%", RED), unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    r1, r2 = st.columns(2)

    with r1:
        vc = dff["Approved_Flag"].value_counts().reset_index()
        vc.columns = ["Flag","Count"]
        fig = px.pie(vc, names="Flag", values="Count", hole=0.55,
                     title="Customer Distribution by Risk Tier",
                     color="Flag", color_discrete_map=C)
        fig.update_traces(textposition='outside', textinfo='percent+label')
        fig.update_layout(height=360, margin=dict(t=50,b=20,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

    with r2:
        if edu_col and score_col:
            edu_grp = dff.groupby(edu_col)[score_col].mean().sort_values().reset_index()
            edu_grp.columns = ["Education","Avg_Credit_Score"]
            fig = px.bar(edu_grp, x="Avg_Credit_Score", y="Education", orientation="h",
                         title="Customers by Education Level (Avg Credit Score)",
                         color="Avg_Credit_Score", color_continuous_scale="Blues",
                         text=edu_grp["Avg_Credit_Score"].round(0))
            fig.update_traces(textposition='outside')
            fig.update_layout(height=360, margin=dict(t=50,b=10,l=10,r=10), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    r3, r4 = st.columns(2)
    with r3:
        if gen_col:
            gvc = dff[gen_col].value_counts().reset_index(); gvc.columns = ["Gender","Count"]
            fig = px.pie(gvc, names="Gender", values="Count", hole=0.5, title="Gender Split",
                         color_discrete_sequence=[BLUE, AMBER])
            fig.update_layout(height=300, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    with r4:
        if mar_col:
            mvc = dff[mar_col].value_counts().reset_index(); mvc.columns = ["Status","Count"]
            fig = px.pie(mvc, names="Status", values="Count", hole=0.5, title="Marital Status Split",
                         color_discrete_sequence=[PURPLE, GREEN])
            fig.update_layout(height=300, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════════════════════════
    # PAGE 2 — Credit & Risk Analysis
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📋 Page 2 — Credit & Risk Analysis")

    cols2 = st.columns(4)
    cols2[0].markdown(metric_card("Avg Credit Score",   f"{dff[score_col].mean():.0f}"  if score_col  else "N/A", BLUE),   unsafe_allow_html=True)
    cols2[1].markdown(metric_card("Avg Delinquencies",  f"{dff[deliq_col].mean():.2f}"  if deliq_col  else "N/A", AMBER),  unsafe_allow_html=True)
    cols2[2].markdown(metric_card("Avg 30+ DPD",        f"{dff[dpd_col].mean():.2f}"    if dpd_col    else "N/A", RED),    unsafe_allow_html=True)
    cols2[3].markdown(metric_card("High Risk %",        f"{high_pct:.1f}%",                                        PURPLE), unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    p2a, p2b = st.columns(2)

    with p2a:
        if score_col and inc_col:
            samp = dff.sample(min(2000, len(dff)), random_state=42)
            fig = px.scatter(samp, x=score_col, y=inc_col, color="Approved_Flag",
                             color_discrete_map=C, opacity=0.55,
                             title="Credit Score vs Monthly Income by Risk Tier")
            fig.update_layout(height=380, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    with p2b:
        if score_col:
            cs = dff.groupby("Approved_Flag")[score_col].mean().reset_index()
            cs.columns = ["Approved_Flag","Avg"]
            cs = cs.sort_values("Avg")
            fig = px.bar(cs, x="Avg", y="Approved_Flag", orientation="h",
                         title="Avg Credit Score by Risk Tier",
                         color="Approved_Flag", color_discrete_map=C,
                         text=cs["Avg"].round(0))
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=320, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    p2c, p2d = st.columns(2)
    with p2c:
        if age_col and deliq_col:
            ad = dff.groupby("Age_Group")[deliq_col].mean().reset_index()
            ad.columns = ["Age_Group","Avg_Deliq"]
            order = ["21-29","30-39","40-49","50-59","60+"]
            ad["Age_Group"] = pd.Categorical(ad["Age_Group"], categories=order, ordered=True)
            ad = ad.sort_values("Age_Group")
            fig = px.line(ad, x="Age_Group", y="Avg_Deliq", markers=True,
                          title="Delinquency Rate by Age Group",
                          color_discrete_sequence=[BLUE], line_shape="spline")
            fig.update_traces(line_width=2.5, marker_size=8)
            fig.update_layout(height=320, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    with p2d:
        enq_map = {"PL": col_find(dff, ["PL_enq","PL_Flag"]),
                   "CC": col_find(dff, ["CC_enq","CC_Flag"]),
                   "AL": col_find(dff, ["AL_Flag"]),
                   "HL": col_find(dff, ["HL_Flag"])}
        enq_data = {k: int(dff[v].sum()) for k,v in enq_map.items() if v}
        if enq_data:
            edf = pd.DataFrame(enq_data.items(), columns=["Product","Count"])
            fig = px.bar(edf, x="Count", y="Product", orientation="h",
                         title="Loan Product Enquiries",
                         color="Product", color_discrete_sequence=[BLUE,GREEN,AMBER,PURPLE],
                         text="Count")
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=320, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════════════════════════
    # PAGE 3 — Trade Line & Payment Analysis
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📋 Page 3 — Trade Line & Payment Analysis")

    cols3 = st.columns(4)
    cols3[0].markdown(metric_card("Avg Missed Payments",  f"{dff[mp_col].mean():.2f}"  if mp_col  else "N/A", RED),    unsafe_allow_html=True)
    cols3[1].markdown(metric_card("Avg Active TL",        f"{dff[act_tl].mean():.2f}"  if act_tl  else "N/A", GREEN),  unsafe_allow_html=True)
    cols3[2].markdown(metric_card("Avg Total TL",         f"{dff[tot_tl].mean():.2f}"  if tot_tl  else "N/A", BLUE),   unsafe_allow_html=True)
    cols3[3].markdown(metric_card("Avg Oldest TL (mths)", f"{dff[old_tl].mean():.1f}"  if old_tl  else "N/A", PURPLE), unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    p3a, p3b = st.columns(2)

    with p3a:
        if mp_col:
            mp = dff.groupby("Approved_Flag")[mp_col].mean().reset_index()
            mp.columns = ["Approved_Flag","Avg_MP"]
            mp = mp.sort_values("Avg_MP")
            fig = px.bar(mp, x="Avg_MP", y="Approved_Flag", orientation="h",
                         title="Avg Missed Payments by Risk Tier",
                         color="Approved_Flag", color_discrete_map=C,
                         text=mp["Avg_MP"].round(2))
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=320, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    with p3b:
        if act_tl and clo_tl:
            tl = dff.groupby("Approved_Flag")[[act_tl, clo_tl]].mean().reset_index()
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Avg Active TL",  x=tl["Approved_Flag"], y=tl[act_tl], marker_color=BLUE))
            fig.add_trace(go.Bar(name="Avg Closed TL",  x=tl["Approved_Flag"], y=tl[clo_tl], marker_color=GREEN))
            fig.update_layout(barmode="group", title="Active vs Closed Trade Lines by Tier",
                              height=320, margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    p3c, p3d = st.columns(2)
    with p3c:
        sec   = col_find(dff, ["Total_Secured_TL","tot_secured_TL"])
        unsec = col_find(dff, ["Total_Unsecured_TL","tot_unsecured_TL"])
        oth   = col_find(dff, ["Total_Other_TL","tot_other_TL"])
        tl_map2 = {k:v for k,v in {"Secured":sec,"Unsecured":unsec,"Other":oth}.items() if v}
        if tl_map2:
            tvals = {k: int(dff[v].sum()) for k,v in tl_map2.items()}
            fig = px.bar(x=list(tvals.keys()), y=list(tvals.values()),
                         title="Secured vs Unsecured vs Other Trade Lines",
                         color=list(tvals.keys()),
                         color_discrete_sequence=[BLUE, AMBER, GREEN],
                         text=[f"{v/1000:.0f}K" for v in tvals.values()])
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=320,
                              xaxis_title="", yaxis_title="Total",
                              margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)

    with p3d:
        if mp_col and "Missed_pmt_band" in dff.columns:
            mpb = dff["Missed_pmt_band"].value_counts().reindex(
                ["0 - None","1 - 2","3 - 5","6+"], fill_value=0).reset_index()
            mpb.columns = ["Band","Count"]
            fig = px.bar(mpb, x="Band", y="Count",
                         title="Missed Payment Distribution",
                         color="Band",
                         color_discrete_sequence=[GREEN, AMBER, AMBER, RED],
                         text="Count")
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=320,
                              xaxis_title="", margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)


def _show_placeholders():
    pages = [
        ("📋 Page 1 — Customer Overview",
         ["Total Customers","Avg Credit Score","Avg Monthly Income","High Risk %"],
         ["Risk Tier Donut","Education vs Credit Score","Gender Split","Marital Status Split"]),
        ("📋 Page 2 — Credit & Risk Analysis",
         ["Avg Credit Score","Avg Delinquencies","Avg 30+ DPD","High Risk %"],
         ["Credit Score vs Income","Avg Score by Risk Tier","Delinquency by Age","Product Enquiries"]),
        ("📋 Page 3 — Trade Line & Payment Analysis",
         ["Avg Missed Payments","Avg Active TL","Avg Total TL","Avg Oldest TL"],
         ["Missed Payments by Tier","Active vs Closed TL","Secured vs Unsecured","Payment Distribution"]),
    ]
    for title, kpis, charts in pages:
        st.markdown(f"---\n### {title}")
        cols = st.columns(4)
        for i, k in enumerate(kpis):
            cols[i].markdown(f"""<div style='background:white;border-radius:12px;padding:1rem;
                box-shadow:0 1px 8px rgba(0,0,0,0.07);border-left:4px solid #e2e8f0;'>
                <div style='font-size:0.72rem;color:#a0aec0;text-transform:uppercase;'>{k}</div>
                <div style='font-size:1.8rem;color:#e2e8f0;font-weight:700;'>—</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("&nbsp;", unsafe_allow_html=True)
        cc = st.columns(2)
        for i, ch in enumerate(charts):
            cc[i%2].markdown(f"""<div style='background:white;border-radius:12px;padding:2.5rem;
                text-align:center;border:2px dashed #e2e8f0;color:#a0aec0;margin-bottom:1rem;'>
                <div style='font-size:2rem;'>📊</div>
                <div style='font-size:0.9rem;margin-top:0.3rem;'>{ch}</div>
            </div>""", unsafe_allow_html=True)
