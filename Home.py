import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Analiză Tranzacții", page_icon="🏦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-box {
    background: #1e293b; border-radius: 10px; padding: 1rem 1.2rem;
    border-left: 4px solid #6366f1; margin-bottom: 0.5rem;
}
.metric-box .lbl { color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-box .val { color: #f1f5f9; font-size: 1.7rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("bank_transactions_data_2_augmented_clean_2.csv")
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], format="mixed", dayfirst=False)
    df["Month"] = df["TransactionDate"].dt.to_period("M").astype(str)
    df["Hour"] = df["TransactionDate"].dt.hour
    return df

df = load_data()

st.title(" Prezentare Generală Tranzacții")
st.markdown(f"Dataset: **{len(df):,}** tranzacții | **{df['AccountID'].nunique()}** conturi | "
            f"**{df['Location'].nunique()}** locații")

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
kpis = [
    (c1, "Total Tranzacții", f"{len(df):,}"),
    (c2, "Volum Total ($)", f"${df['TransactionAmount'].sum():,.0f}"),
    (c3, "Amount Mediu ($)", f"${df['TransactionAmount'].mean():,.2f}"),
    (c4, "Conturi Unice", f"{df['AccountID'].nunique()}"),
]
for col, label, val in kpis:
    with col:
        st.markdown(f'<div class="metric-box"><div class="lbl">{label}</div><div class="val">{val}</div></div>',
                    unsafe_allow_html=True)

st.divider()

# ── Grafice ────────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    monthly = df.groupby("Month")["TransactionAmount"].sum().reset_index()
    fig = px.bar(monthly, x="Month", y="TransactionAmount",
                 title="💰 Volum total pe lună",
                 labels={"TransactionAmount": "Volum ($)", "Month": "Lună"},
                 color_discrete_sequence=["#6366f1"], template="plotly_dark")
    fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    channel = df["Channel"].value_counts().reset_index()
    channel.columns = ["Canal", "Nr. Tranzacții"]
    fig = px.pie(channel, names="Canal", values="Nr. Tranzacții",
                 title="📡 Distribuție pe canal",
                 template="plotly_dark", hole=0.4,
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(paper_bgcolor="#0f172a")
    st.plotly_chart(fig, use_container_width=True)

# Distribuție amount
fig = px.histogram(df, x="TransactionAmount", nbins=60,
                   title="📊 Distribuția sumelor tranzacționate",
                   labels={"TransactionAmount": "Sumă ($)", "count": "Nr. tranzacții"},
                   color_discrete_sequence=["#34d399"], template="plotly_dark")
fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
st.plotly_chart(fig, use_container_width=True)