import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Analiză pe Locații", page_icon="🌍", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("bank_transactions_data_2_augmented_clean_2.csv")
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], format="mixed", dayfirst=False)
    df["Month"] = df["TransactionDate"].dt.to_period("M").astype(str)
    df["Hour"] = df["TransactionDate"].dt.hour
    return df

df = load_data()

st.title("Analiză pe Locații")
st.markdown("Distribuția tranzacțiilor și sumelor pe orașele din SUA.")

top_n = st.slider("Afișează top N orașe", 5, 30, 15)

loc_stats = (
    df.groupby("Location")
    .agg(NrTranzactii=("TransactionID", "count"),
         VolumTotal=("TransactionAmount", "sum"),
         AmountMediu=("TransactionAmount", "mean"))
    .reset_index()
    .sort_values("NrTranzactii", ascending=False)
    .head(top_n)
)

col_a, col_b = st.columns(2)

with col_a:
    fig = px.bar(loc_stats.sort_values("NrTranzactii"),
                 x="NrTranzactii", y="Location", orientation="h",
                 title=f"Top {top_n} orașe – Nr. Tranzacții",
                 color_discrete_sequence=["#6366f1"], template="plotly_dark",
                 labels={"NrTranzactii": "Nr. Tranzacții", "Location": "Oraș"})
    fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    fig = px.bar(loc_stats.sort_values("VolumTotal"),
                 x="VolumTotal", y="Location", orientation="h",
                 title=f"Top {top_n} orașe – Volum Total ($)",
                 color="AmountMediu", color_continuous_scale="Plasma",
                 template="plotly_dark",
                 labels={"VolumTotal": "Volum ($)", "Location": "Oraș", "AmountMediu": "Amount Mediu"})
    fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
    st.plotly_chart(fig, use_container_width=True)


loc_type = (
    df[df["Location"].isin(loc_stats["Location"].head(10))]
    .groupby(["Location", "TransactionType"])["TransactionID"]
    .count()
    .reset_index()
    .rename(columns={"TransactionID": "Count"})
)
fig = px.bar(loc_type, x="Location", y="Count", color="TransactionType",
             barmode="stack", title="Debit vs Credit pe top 10 orașe",
             template="plotly_dark", color_discrete_sequence=["#6366f1", "#34d399"],
             labels={"Count": "Nr. Tranzacții", "Location": "Oraș", "TransactionType": "Tip"})
fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", xaxis_tickangle=-30)
st.plotly_chart(fig, use_container_width=True)
