import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import io

# ── Palette ──────────────────────────────────────────────────────────────────
BLUE   = "#3182ce"
GREEN  = "#38a169"
RED    = "#e53e3e"
AMBER  = "#d69e2e"
PURPLE = "#805ad5"
PALETTE = [BLUE, GREEN, RED, AMBER, PURPLE, "#dd6b20"]

sns.set_theme(style="whitegrid", font="DejaVu Sans")
plt.rcParams.update({"figure.facecolor": "none", "axes.facecolor": "#f7f8fc",
                     "axes.spines.top": False, "axes.spines.right": False})

# ── Helpers ──────────────────────────────────────────────────────────────────
SENTINEL_COLS = ['CC_utilization','PL_utilization','time_since_recent_deliquency',
                 'max_delinquency_level','time_since_first_deliquency','max_unsec_exposure_inPct']
IMPUTE_COLS   = ['max_deliq_6mts','max_deliq_12mts','time_since_recent_enq','enq_L3m',
                 'enq_L6m','enq_L12m','PL_enq_L6m','PL_enq_L12m','PL_enq','CC_enq_L6m',
                 'CC_enq','tot_enq','CC_enq_L12m','time_since_recent_payment',
                 'Age_Oldest_TL','Age_Newest_TL','pct_currentBal_all_TL']

def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.replace(-99999, np.nan, inplace=True)
    drop = [c for c in SENTINEL_COLS if c in df.columns]
    df.drop(columns=drop, inplace=True, errors='ignore')
    fill0 = [c for c in ['max_deliq_6mts','max_deliq_12mts'] if c in df.columns]
    df[fill0] = df[fill0].fillna(0)
    imp = [c for c in IMPUTE_COLS if c in df.columns]
    df[imp] = df[imp].fillna(df[imp].median())
    return df

def fig_to_st(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130)
    buf.seek(0)
    st.image(buf, use_column_width=True)
    plt.close(fig)

# ── Main ─────────────────────────────────────────────────────────────────────
def show():
    st.markdown("""
    <div class='page-header'>
        <h1>📊 Exploratory Data Analysis</h1>
        <p>Upload your customer loan dataset to explore distributions, correlations, and data quality.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Upload ───────────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Upload Dataset</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        file1 = st.file_uploader("External CIBIL Data (CSV / Excel)", type=["csv","xlsx","xls"], key="ext")
        file2 = st.file_uploader("Internal Bank Data (CSV / Excel) — optional merge", type=["csv","xlsx","xls"], key="int")

    def read_file(f):
        if f.name.endswith(".csv"):
            return pd.read_csv(f)
        return pd.read_excel(f)

    if file1 is None:
        st.markdown("<div class='callout'>👆 Upload at least one CSV or Excel file to begin analysis.</div>", unsafe_allow_html=True)
        return

    df_ext = read_file(file1)

    if file2:
        df_int = read_file(file2)
        if "PROSPECTID" in df_ext.columns and "PROSPECTID" in df_int.columns:
            df = pd.merge(df_ext, df_int, on="PROSPECTID", how="inner")
            st.success(f"✅ Merged on PROSPECTID → {df.shape[0]:,} rows, {df.shape[1]} columns")
        else:
            df = pd.concat([df_ext, df_int], axis=1)
            st.warning("PROSPECTID not found in both files — concatenated side by side.")
    else:
        df = df_ext

    df_clean = clean(df)

    # ── Overview Metrics ─────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Dataset Overview</div>", unsafe_allow_html=True)
    null_pct = df_clean.isnull().mean().mean() * 100
    num_cols  = df_clean.select_dtypes("number").shape[1]
    cat_cols  = df_clean.select_dtypes("object").shape[1]

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><h3>Total Records</h3><p class='value'>{df_clean.shape[0]:,}</p><p class='sub'>rows after cleaning</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card green'><h3>Features</h3><p class='value'>{df_clean.shape[1]}</p><p class='sub'>{num_cols} numeric · {cat_cols} categorical</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card amber'><h3>Null Rate</h3><p class='value'>{null_pct:.1f}%</p><p class='sub'>after sentinel treatment</p></div>", unsafe_allow_html=True)
    dropped = len([c for c in SENTINEL_COLS if c in df.columns])
    c4.markdown(f"<div class='metric-card red'><h3>Cols Dropped</h3><p class='value'>{dropped}</p><p class='sub'>&gt;40% sentinel values</p></div>", unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    with st.expander("📋 Raw Data Preview (first 100 rows)"):
        st.dataframe(df_clean.head(100), use_container_width=True)

    with st.expander("📐 Statistical Summary"):
        st.dataframe(df_clean.describe().T.style.format("{:.2f}"), use_container_width=True)

    # ── Target Distribution ──────────────────────────────────────────────────
    target_col = None
    for c in ["Approved_Flag","approved_flag","TARGET","target","label"]:
        if c in df_clean.columns:
            target_col = c
            break

    if target_col:
        st.markdown("<div class='section-title'>Target Variable Distribution</div>", unsafe_allow_html=True)
        vc = df_clean[target_col].value_counts()

        cola, colb = st.columns([1, 2])
        with cola:
            st.dataframe(vc.rename("Count").reset_index().rename(columns={"index": target_col}), use_container_width=True)

        with colb:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            bars = ax.bar(vc.index, vc.values, color=PALETTE[:len(vc)], edgecolor="white", width=0.55, zorder=3)
            ax.bar_label(bars, fmt="%d", padding=4, fontsize=10)
            ax.set_xlabel(target_col, fontsize=11)
            ax.set_ylabel("Count", fontsize=11)
            ax.set_title("Approval Class Distribution", fontsize=13, fontweight="bold")
            ax.grid(axis="y", alpha=0.4, zorder=0)
            fig_to_st(fig)

    # ── Numeric Distributions ────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Numeric Feature Distributions</div>", unsafe_allow_html=True)
    num_df = df_clean.select_dtypes("number")
    num_cols_list = [c for c in num_df.columns if c not in ["PROSPECTID"]]

    selected = st.multiselect("Choose features to plot", num_cols_list,
                              default=num_cols_list[:6] if len(num_cols_list) >= 6 else num_cols_list)

    if selected:
        n = len(selected)
        ncols = 3
        nrows = (n + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(14, 3.5 * nrows))
        axes = np.array(axes).flatten() if n > 1 else [axes]

        for i, col in enumerate(selected):
            ax = axes[i]
            data = df_clean[col].dropna()
            ax.hist(data, bins=30, color=PALETTE[i % len(PALETTE)], edgecolor="white", alpha=0.85, zorder=3)
            ax.set_title(col, fontsize=10, fontweight="bold")
            ax.set_xlabel("")
            ax.grid(axis="y", alpha=0.3, zorder=0)

        for j in range(i+1, len(axes)):
            axes[j].set_visible(False)

        fig.tight_layout(pad=2)
        fig_to_st(fig)

    # ── Correlation Heatmap ──────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Correlation Heatmap</div>", unsafe_allow_html=True)
    corr = num_df[[c for c in num_df.columns if c not in ["PROSPECTID"]]].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    fig, ax = plt.subplots(figsize=(14, 9))
    sns.heatmap(corr, mask=mask, cmap="RdBu_r", center=0, ax=ax,
                linewidths=0.3, linecolor="white", vmin=-1, vmax=1,
                annot=(len(corr) <= 15), fmt=".1f", annot_kws={"size": 7})
    ax.set_title("Feature Correlation Matrix", fontsize=13, fontweight="bold", pad=12)
    fig_to_st(fig)

    # Highly correlated pairs
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    high = upper.stack()
    high = high[high.abs() > 0.7].sort_values(ascending=False)
    if len(high):
        with st.expander(f"⚠️ {len(high)} highly correlated feature pairs (|r| > 0.7)"):
            st.dataframe(high.rename("Correlation").reset_index().rename(
                columns={"level_0": "Feature A", "level_1": "Feature B"}), use_container_width=True)

    # ── Categorical Columns ──────────────────────────────────────────────────
    cat_df = df_clean.select_dtypes("object")
    if not cat_df.empty:
        st.markdown("<div class='section-title'>Categorical Feature Distributions</div>", unsafe_allow_html=True)
        cat_list = cat_df.columns.tolist()
        n = len(cat_list)
        ncols = min(n, 3)
        nrows = (n + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(14, 3.8 * nrows))
        axes = np.array(axes).flatten() if n > 1 else [axes]

        for i, col in enumerate(cat_list):
            ax = axes[i]
            vc = df_clean[col].value_counts().head(10)
            ax.barh(vc.index[::-1], vc.values[::-1], color=PALETTE[i % len(PALETTE)], alpha=0.85, zorder=3)
            ax.set_title(col, fontsize=10, fontweight="bold")
            ax.grid(axis="x", alpha=0.3, zorder=0)

        for j in range(i+1, len(axes)):
            axes[j].set_visible(False)

        fig.tight_layout(pad=2)
        fig_to_st(fig)

    # ── Missing Values ───────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Missing Value Analysis</div>", unsafe_allow_html=True)
    miss = df_clean.isnull().sum()
    miss = miss[miss > 0].sort_values(ascending=False)
    if miss.empty:
        st.success("✅ No missing values in the cleaned dataset.")
    else:
        fig, ax = plt.subplots(figsize=(10, max(3, len(miss) * 0.4)))
        pct = (miss / len(df_clean) * 100)
        ax.barh(miss.index[::-1], pct.values[::-1], color=RED, alpha=0.7, zorder=3)
        ax.set_xlabel("Missing %", fontsize=11)
        ax.set_title("Columns with Missing Values", fontsize=13, fontweight="bold")
        ax.grid(axis="x", alpha=0.3, zorder=0)
        fig.tight_layout()
        fig_to_st(fig)
