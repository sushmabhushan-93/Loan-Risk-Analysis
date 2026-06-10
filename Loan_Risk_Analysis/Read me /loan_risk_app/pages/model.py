import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io, pickle, warnings
import seaborn as sns
warnings.filterwarnings("ignore")

from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, accuracy_score,
                              roc_auc_score, roc_curve, confusion_matrix)

# ── Palette ──────────────────────────────────────────────────────────────────
BLUE = "#3182ce"; GREEN = "#38a169"; RED = "#e53e3e"; AMBER = "#d69e2e"
plt.rcParams.update({"figure.facecolor": "none", "axes.facecolor": "#f7f8fc",
                     "axes.spines.top": False, "axes.spines.right": False})

def fig_to_st(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130)
    buf.seek(0)
    st.image(buf, use_column_width=True)
    plt.close(fig)

SENTINEL_COLS = ['CC_utilization','PL_utilization','time_since_recent_deliquency',
                 'max_delinquency_level','time_since_first_deliquency','max_unsec_exposure_inPct']
IMPUTE_COLS = ['max_deliq_6mts','max_deliq_12mts','time_since_recent_enq','enq_L3m',
               'enq_L6m','enq_L12m','PL_enq_L6m','PL_enq_L12m','PL_enq','CC_enq_L6m',
               'CC_enq','tot_enq','CC_enq_L12m','time_since_recent_payment',
               'Age_Oldest_TL','Age_Newest_TL','pct_currentBal_all_TL']
EDU_ORDER = {'OTHERS':0,'SSC':1,'12TH':2,'GRADUATE':3,'UNDER GRADUATE':3,
             'POST-GRADUATE':4,'PROFESSIONAL':5}

# ── Pipeline ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="⚙️ Training models — this may take ~30 sec…")
def run_pipeline(data_bytes_ext, data_bytes_int=None):
    import io as _io
    ext_df = pd.read_csv(_io.BytesIO(data_bytes_ext)) if data_bytes_ext else None
    if ext_df is None:
        return None

    int_df = pd.read_csv(_io.BytesIO(data_bytes_int)) if data_bytes_int else None

    if int_df is not None and "PROSPECTID" in ext_df.columns and "PROSPECTID" in int_df.columns:
        df = pd.merge(ext_df, int_df, on="PROSPECTID", how="inner")
    else:
        df = ext_df.copy()

    # Clean
    df.replace(-99999, np.nan, inplace=True)
    drop_c = [c for c in SENTINEL_COLS if c in df.columns]
    df.drop(columns=drop_c, inplace=True, errors='ignore')
    fill0 = [c for c in ['max_deliq_6mts','max_deliq_12mts'] if c in df.columns]
    df[fill0] = df[fill0].fillna(0)
    imp_c = [c for c in IMPUTE_COLS if c in df.columns]
    df[imp_c] = df[imp_c].fillna(df[imp_c].median())

    # Target
    if "Approved_Flag" not in df.columns:
        return {"error": "Column 'Approved_Flag' not found in data."}
    df['Target'] = np.where(df['Approved_Flag'].isin(['P3','P4']), 1, 0)

    # Encode
    if 'EDUCATION' in df.columns:
        df['EDUCATION'] = df['EDUCATION'].map(EDU_ORDER)
    ohe_cols = [c for c in ['MARITALSTATUS','GENDER','last_prod_enq2','first_prod_enq2'] if c in df.columns]
    df = pd.get_dummies(df, columns=ohe_cols, drop_first=True)

    drop_cols = ["PROSPECTID","Approved_Flag","Target"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df['Target']

    Xtrain, Xtest, ytrain, ytest = train_test_split(X, y, test_size=0.2, random_state=42)
    ss = StandardScaler()
    Xtrain_s = ss.fit_transform(Xtrain)
    Xtest_s  = ss.transform(Xtest)

    # RFE
    lr_rfe = LogisticRegression(max_iter=500, random_state=42)
    rfe = RFE(lr_rfe, n_features_to_select=8)
    rfe.fit(Xtrain_s, ytrain)
    top_features = list(X.columns[rfe.support_])

    rfe_df = pd.DataFrame({'Feature': X.columns, 'Rank': rfe.ranking_}).sort_values('Rank')

    # Logistic Regression (top 8)
    X_top = df[top_features]
    XTrain, XTest, yTrain, yTest = train_test_split(X_top, y, test_size=0.2, random_state=42)
    XTrain_s = ss.fit_transform(XTrain)
    XTest_s  = ss.transform(XTest)

    lr = LogisticRegression(max_iter=500, random_state=42)
    lr.fit(XTrain_s, yTrain)
    lr_pred  = lr.predict(XTest_s)
    lr_prob  = lr.predict_proba(XTest_s)[:,1]
    lr_acc   = accuracy_score(yTest, lr_pred)
    lr_auc   = roc_auc_score(yTest, lr_prob)
    lr_report= classification_report(yTest, lr_pred, output_dict=True)
    lr_cm    = confusion_matrix(yTest, lr_pred)
    lr_fpr, lr_tpr, _ = roc_curve(yTest, lr_prob)
    lr_cv    = cross_val_score(lr, X_top, y, cv=5, scoring='roc_auc')

    # Random Forest (top 8)
    rf = RandomForestClassifier(max_depth=10, min_samples_leaf=20,
                                 n_estimators=200, class_weight='balanced', random_state=42)
    rf.fit(XTrain_s, yTrain)
    rf_pred  = rf.predict(XTest_s)
    rf_prob  = rf.predict_proba(XTest_s)[:,1]
    rf_acc   = accuracy_score(yTest, rf_pred)
    rf_auc   = roc_auc_score(yTest, rf_prob)
    rf_report= classification_report(yTest, rf_pred, output_dict=True)
    rf_cm    = confusion_matrix(yTest, rf_pred)
    rf_fpr, rf_tpr, _ = roc_curve(yTest, rf_prob)

    # Save model
    model_bytes = pickle.dumps({"model": lr, "scaler": ss, "features": top_features})

    return dict(
        top_features=top_features, rfe_df=rfe_df,
        lr_acc=lr_acc, lr_auc=lr_auc, lr_report=lr_report, lr_cm=lr_cm,
        lr_fpr=lr_fpr, lr_tpr=lr_tpr, lr_cv=lr_cv,
        rf_acc=rf_acc, rf_auc=rf_auc, rf_report=rf_report, rf_cm=rf_cm,
        rf_fpr=rf_fpr, rf_tpr=rf_tpr,
        model_bytes=model_bytes,
        ss=ss, lr_model=lr, top_features_list=top_features
    )

# ── Show ──────────────────────────────────────────────────────────────────────
def show():
    st.markdown("""
    <div class='page-header'>
        <h1>🤖 Predictive Model</h1>
        <p>Train, compare, and download Logistic Regression &amp; Random Forest models for loan risk classification.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Upload ───────────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Upload Training Data</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        f_ext = st.file_uploader("External CIBIL Data (must have Approved_Flag)", type=["csv","xlsx"], key="m_ext")
    with c2:
        f_int = st.file_uploader("Internal Bank Data (optional)", type=["csv","xlsx"], key="m_int")

    if f_ext is None:
        st.markdown("<div class='callout'>👆 Upload the CIBIL CSV/Excel file containing <strong>Approved_Flag</strong> to train the models.</div>", unsafe_allow_html=True)
        return

    def to_csv_bytes(f):
        if f.name.endswith(".csv"):
            return f.read()
        df = pd.read_excel(f)
        return df.to_csv(index=False).encode()

    ext_bytes = to_csv_bytes(f_ext)
    int_bytes = to_csv_bytes(f_int) if f_int else None

    if st.button("🚀 Train Models", type="primary"):
        st.session_state.pop("results", None)

    if "results" not in st.session_state:
        with st.spinner("Training in progress…"):
            res = run_pipeline(ext_bytes, int_bytes)
            st.session_state["results"] = res
    else:
        res = st.session_state["results"]

    if res is None or "error" in res:
        st.error(res.get("error","Unknown error during training.") if res else "Training failed.")
        return

    st.success("✅ Models trained successfully!")

    # ── Feature Selection ────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Feature Selection — RFE Top 8</div>", unsafe_allow_html=True)
    cols = st.columns([1,2])
    with cols[0]:
        rfe_show = res["rfe_df"].head(15).copy()
        rfe_show["Selected"] = rfe_show["Feature"].isin(res["top_features"]).map({True:"✅", False:""})
        st.dataframe(rfe_show, hide_index=True, use_container_width=True)
    with cols[1]:
        top = res["rfe_df"][res["rfe_df"]["Feature"].isin(res["top_features"])]
        fig, ax = plt.subplots(figsize=(6,4))
        ax.barh(top["Feature"][::-1], [1]*len(top), color=BLUE, alpha=0.8, zorder=3)
        ax.set_xlabel("")
        ax.set_xlim(0, 1.5)
        ax.set_title("RFE-Selected Features (Top 8)", fontsize=12, fontweight="bold")
        ax.set_xticks([])
        ax.grid(False)
        for i, feat in enumerate(top["Feature"][::-1]):
            ax.text(0.05, i, feat, va="center", fontsize=10, color="white", fontweight="bold")
        fig_to_st(fig)

    # ── Model Comparison ─────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Model Comparison</div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"<div class='metric-card'><h3>LR Accuracy</h3><p class='value'>{res['lr_acc']:.1%}</p><p class='sub'>Logistic Regression</p></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card green'><h3>LR AUC-ROC</h3><p class='value'>{res['lr_auc']:.3f}</p><p class='sub'>Logistic Regression</p></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-card amber'><h3>RF Accuracy</h3><p class='value'>{res['rf_acc']:.1%}</p><p class='sub'>Random Forest</p></div>", unsafe_allow_html=True)
    m4.markdown(f"<div class='metric-card red'><h3>RF AUC-ROC</h3><p class='value'>{res['rf_auc']:.3f}</p><p class='sub'>Random Forest</p></div>", unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ROC Curves + Confusion Matrices
    tab1, tab2, tab3 = st.tabs(["📉 ROC Curves", "🟦 Confusion Matrices", "📋 Classification Reports"])

    with tab1:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(res['lr_fpr'], res['lr_tpr'], color=BLUE, lw=2, label=f"Logistic Regression (AUC={res['lr_auc']:.3f})")
        ax.plot(res['rf_fpr'], res['rf_tpr'], color=GREEN, lw=2, label=f"Random Forest (AUC={res['rf_auc']:.3f})")
        ax.plot([0,1],[0,1],'--', color='#a0aec0', lw=1)
        ax.set_xlabel("False Positive Rate", fontsize=11)
        ax.set_ylabel("True Positive Rate", fontsize=11)
        ax.set_title("ROC Curves", fontsize=13, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(alpha=0.3)
        fig_to_st(fig)

    with tab2:
        fc1, fc2 = st.columns(2)
        for col, cm, title, color in [(fc1, res['lr_cm'], "Logistic Regression", BLUE),
                                       (fc2, res['rf_cm'], "Random Forest", GREEN)]:
            with col:
                fig, ax = plt.subplots(figsize=(4.5, 3.5))
                sns_ax = sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                            xticklabels=["Low Risk","High Risk"],
                            yticklabels=["Low Risk","High Risk"],
                            linewidths=0.5, linecolor="white")
                ax.set_title(title, fontsize=12, fontweight="bold")
                ax.set_ylabel("Actual", fontsize=10)
                ax.set_xlabel("Predicted", fontsize=10)
                fig_to_st(fig)

    with tab3:
        rc1, rc2 = st.columns(2)
        for col, rpt, title in [(rc1, res['lr_report'], "Logistic Regression"),
                                  (rc2, res['rf_report'], "Random Forest")]:
            with col:
                st.write(f"**{title}**")
                rpt_df = pd.DataFrame(rpt).T.drop(index=['accuracy'], errors='ignore')
                st.dataframe(rpt_df.style.format("{:.2f}"), use_container_width=True)

    # ── Cross Validation ─────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Cross-Validation (Logistic Regression, 5-Fold AUC)</div>", unsafe_allow_html=True)
    cv_scores = res['lr_cv']
    cc = st.columns(len(cv_scores) + 1)
    for i, s in enumerate(cv_scores):
        cc[i].metric(f"Fold {i+1}", f"{s:.3f}")
    cc[-1].metric("Mean ± Std", f"{cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # ── Single Prediction ────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Single Applicant Prediction</div>", unsafe_allow_html=True)
    st.markdown("<div class='callout'>Enter values for the top 8 selected features to get an instant risk prediction.</div>", unsafe_allow_html=True)

    features = res["top_features_list"]
    input_vals = {}
    cols_per_row = 4
    for i in range(0, len(features), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for j, feat in enumerate(features[i:i+cols_per_row]):
            with row_cols[j]:
                input_vals[feat] = st.number_input(feat, value=0.0, key=f"inp_{feat}")

    if st.button("🔍 Predict Risk", type="primary"):
        inp_df = pd.DataFrame([input_vals])
        ss = res["ss"]
        lr_model = res["lr_model"]
        inp_s = ss.transform(inp_df)
        pred = lr_model.predict(inp_s)[0]
        prob = lr_model.predict_proba(inp_s)[0][1]

        if pred == 1:
            st.markdown(f"""
            <div class='pred-box' style='border: 2px solid {RED};'>
                <div class='risk-label' style='color:{RED};'>⚠️ HIGH RISK</div>
                <div style='color:#718096; margin-top:0.5rem;'>Risk Probability: <strong>{prob:.1%}</strong></div>
                <div style='margin-top:0.5rem;'><span class='badge badge-high'>P3 / P4 — Likely to default</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='pred-box' style='border: 2px solid {GREEN};'>
                <div class='risk-label' style='color:{GREEN};'>✅ LOW RISK</div>
                <div style='color:#718096; margin-top:0.5rem;'>Risk Probability: <strong>{prob:.1%}</strong></div>
                <div style='margin-top:0.5rem;'><span class='badge badge-low'>P1 / P2 — Creditworthy applicant</span></div>
            </div>
            """, unsafe_allow_html=True)

    # ── Download Model ───────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Download Trained Model</div>", unsafe_allow_html=True)
    st.download_button(
        label="⬇️ Download loan_model.pkl",
        data=res["model_bytes"],
        file_name="loan_model.pkl",
        mime="application/octet-stream"
    )
    st.markdown("<div style='font-size:0.85rem; color:#718096;'>The pickle contains the trained Logistic Regression model, StandardScaler, and selected feature names.</div>", unsafe_allow_html=True)
