import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Detecție Fraude", page_icon="🚨", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.alert-red    { background:#450a0a; border-left:4px solid #ef4444; border-radius:8px; padding:0.8rem 1rem; margin:0.5rem 0; color:#fca5a5; }
.alert-yellow { background:#422006; border-left:4px solid #f59e0b; border-radius:8px; padding:0.8rem 1rem; margin:0.5rem 0; color:#fcd34d; }
.stat { background:#1e293b; border-radius:8px; padding:0.8rem 1rem; text-align:center; }
.stat .n { font-size:1.8rem; font-weight:700; color:#f87171; }
.stat .l { font-size:0.75rem; color:#94a3b8; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("bank_transactions_data_2_augmented_clean_2.csv")
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], format="mixed", dayfirst=False)
    return df

df = load_data()

# ─── Parametri sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Parametri")
    std_mult = st.slider("Prag anomalie amount (× std)", 2.0, 5.0, 3.0, 0.5)
    velocity_hours = st.slider("Fereastră velocity fraud (ore)", 1, 6, 2)

st.title(" Detecție Fraude")
st.markdown("Metode statistice simple, **fără machine learning**.")




st.subheader(f" Velocity Fraud – locații diferite în mai puțin de {velocity_hours}h")
st.markdown(f"""
<div class='alert-red'>
<b>Logică:</b> Dacă același AccountID face tranzacții în <b>orașe diferite</b> cu mai puțin de
<b>{velocity_hours} ore</b> între ele, este probabil imposibil fizic → fraudă.
<br><b>Nu se consideră fraudă</b> dacă locațiile sunt aceleași sau dacă diferența de timp e mai mare de {velocity_hours}h.
</div>
""", unsafe_allow_html=True)

@st.cache_data
def detect_velocity(hours_window):
    sorted_df = df[["AccountID", "TransactionID", "TransactionDate", "Location", "TransactionAmount", "DeviceID", "IP Address"]].sort_values(
        ["AccountID", "TransactionDate"]
    )
    velocity_cases = []
    for acc_id, group in sorted_df.groupby("AccountID"):
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            t1, t2 = group.loc[i], group.loc[i + 1]
            diff_hours = (t2["TransactionDate"] - t1["TransactionDate"]).total_seconds() / 3600
            if 0 < diff_hours <= hours_window and t1["Location"] != t2["Location"]:
                velocity_cases.append({
                    "AccountID": acc_id,
                    "Tranzacție 1": t1["TransactionID"],
                    "Locație 1": t1["Location"],
                    "Timp 1": t1["TransactionDate"].strftime("%d/%m/%Y %H:%M"),
                    "Tranzacție 2": t2["TransactionID"],
                    "Locație 2": t2["Location"],
                    "Timp 2": t2["TransactionDate"].strftime("%d/%m/%Y %H:%M"),
                    "Diferență (min)": round(diff_hours * 60, 0),
                    "Amount 1 ($)": t1["TransactionAmount"],
                    "Amount 2 ($)": t2["TransactionAmount"],
                })
    return pd.DataFrame(velocity_cases)

with st.spinner("Calculez velocity fraud..."):
    velocity_df = detect_velocity(velocity_hours)

if len(velocity_df) == 0:
    st.success(f"Nu s-au găsit cazuri de velocity fraud în fereastra de {velocity_hours}h.")
else:
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="stat"><div class="n">{len(velocity_df)}</div><div class="l">Perechi suspecte</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat"><div class="n">{velocity_df["AccountID"].nunique()}</div><div class="l">Conturi implicate</div></div>', unsafe_allow_html=True)

    st.dataframe(velocity_df.sort_values("Diferență (min)"), use_container_width=True, hide_index=True)

  
    loc_counts = pd.concat([velocity_df["Locație 1"], velocity_df["Locație 2"]]).value_counts().head(10).reset_index()
    loc_counts.columns = ["Locație", "Apariții"]
    fig = px.bar(loc_counts, x="Locație", y="Apariții",
                 title="Top locații implicate în velocity fraud",
                 color_discrete_sequence=["#f87171"], template="plotly_dark")
    fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
    st.plotly_chart(fig, use_container_width=True)

st.divider()


st.subheader(f" Anomalii Amount (medie + {std_mult}× deviație standard)")
st.markdown(f"""
<div class='alert-yellow'>
<b>Logică:</b> Se calculează <b>media</b> și <b>deviația standard</b> a sumelor pentru fiecare cont.
Dacă o tranzacție depășește <code>medie + {std_mult}× std</code>, este marcată ca anomalie.
Aceasta detectează tranzacții neobișnuit de mari față de comportamentul normal al contului.
</div>
""", unsafe_allow_html=True)

acc_stats = (
    df.groupby("AccountID")["TransactionAmount"]
    .agg(["mean", "std"]).reset_index()
    .rename(columns={"mean": "Medie", "std": "Std"})
)
acc_stats["Std"] = acc_stats["Std"].fillna(0)
merged = df.merge(acc_stats, on="AccountID")
merged["Prag"] = merged["Medie"] + std_mult * merged["Std"]
anomalii = merged[merged["TransactionAmount"] > merged["Prag"]].copy()
anomalii["Depășire (×std)"] = ((anomalii["TransactionAmount"] - anomalii["Medie"]) / anomalii["Std"].replace(0, np.nan)).round(2)

c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="stat"><div class="n" style="color:#fbbf24">{len(anomalii):,}</div><div class="l">Anomalii detectate</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat"><div class="n" style="color:#fbbf24">{anomalii["AccountID"].nunique()}</div><div class="l">Conturi implicate</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat"><div class="n" style="color:#fbbf24">{anomalii["Depășire (×std)"].mean():.1f}σ</div><div class="l">Depășire medie</div></div>', unsafe_allow_html=True)

display_cols = {
    "TransactionID": "ID Tranzacție",
    "AccountID": "Cont",
    "TransactionAmount": "Sumă ($)",
    "Medie": "Medie Cont ($)",
    "Prag": "Prag ($)",
    "Depășire (×std)": "Depășire (×std)",
    "Location": "Locație",
    "Channel": "Canal",
    "TransactionDate": "Data"
}
show = anomalii[list(display_cols.keys())].rename(columns=display_cols)
show["Data"] = pd.to_datetime(show["Data"]).dt.strftime("%d/%m/%Y %H:%M")
st.dataframe(
    show.sort_values("Depășire (×std)", ascending=False).head(50).reset_index(drop=True),
    use_container_width=True, hide_index=True
)

csv = anomalii[list(display_cols.keys())].rename(columns=display_cols).to_csv(index=False).encode("utf-8")
st.download_button("Descarcă anomalii CSV", data=csv, file_name="anomalii_amount.csv", mime="text/csv")
