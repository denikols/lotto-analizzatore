
import streamlit as st
import pandas as pd
from collections import Counter

st.title("📊 Analisi Frequenza Storica nei 5 Colpi Successivi")

uploaded_file = st.file_uploader("Carica il file CSV delle estrazioni", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, skiprows=3)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.sort_values("Data")

    ruote = ["Bari", "Cagliari", "Firenze", "Genova", "Milano",
             "Napoli", "Palermo", "Roma", "Torino", "Venezia", "Nazionale"]

    ruota = st.selectbox("Scegli la ruota", ruote)
    data_selezionata = st.date_input("Scegli la data base da analizzare", value=df["Data"].max().date(),
                                     min_value=df["Data"].min().date(), max_value=df["Data"].max().date())

    riga_base = df[df["Data"] == pd.to_datetime(data_selezionata)]

    if riga_base.empty:
        st.warning("Nessuna estrazione trovata per la data selezionata.")
        st.stop()

    try:
        estratti = riga_base[[ruota, f"{ruota}.1", f"{ruota}.2", f"{ruota}.3", f"{ruota}.4"]].iloc[0].tolist()
        estratti = [int(n) for n in estratti if pd.notnull(n)]
    except:
        st.error("Errore nella lettura dei numeri.")
        st.stop()

    successivi = []
    for num in estratti:
        successivi.extend([
            num - 1 if num > 1 else 90,
            num + 1 if num < 90 else 1
        ])
    numeri_finali = sorted(set(estratti + successivi))

    st.markdown("### 🎯 15 Numeri Finali da Analizzare")
    st.write(numeri_finali)

    # ANALISI STATISTICA STORICA
    frequenze = {num: 0 for num in numeri_finali}
    tutte_le_date = df[df["Data"] < pd.to_datetime(data_selezionata)]["Data"].unique()

    for data in tutte_le_date:
        row = df[df["Data"] == data]
        if row.empty:
            continue

        try:
            base = row[[ruota, f"{ruota}.1", f"{ruota}.2", f"{ruota}.3", f"{ruota}.4"]].iloc[0].tolist()
            base = [int(n) for n in base if pd.notnull(n)]
        except:
            continue

        vicini = []
        for n in base:
            vicini.extend([
                n - 1 if n > 1 else 90,
                n + 1 if n < 90 else 1
            ])
        numeri_analizzati = sorted(set(base + vicini))

        successive = df[df["Data"] > data].sort_values("Data").head(5)
        if successive.empty:
            continue

        for _, r in successive.iterrows():
            estratti_successivi = [r[f"{ruota}"], r[f"{ruota}.1"], r[f"{ruota}.2"], r[f"{ruota}.3"], r[f"{ruota}.4"]]
            estratti_successivi = [int(n) for n in estratti_successivi if pd.notnull(n)]
            for num in numeri_finali:
                if num in estratti_successivi:
                    frequenze[num] += 1

    df_freq = pd.DataFrame(list(frequenze.items()), columns=["Numero", "Presenze nei 5 colpi successivi"])
    df_freq = df_freq.sort_values("Presenze nei 5 colpi successivi", ascending=False).reset_index(drop=True)

    


    # Evidenziazione e mostra numeri della data selezionata
    st.markdown("### 📆 Numeri estratti nella data selezionata")
    st.write(f"**{data_selezionata.strftime('%d/%m/%Y')} - {ruota}:**", estratti)

    def colore_numero(row):
        num = row["Numero"]
        if num in estratti:
            return "color: red; font-weight: bold; font-size: 16px; text-align: center;"
        elif num in successivi:
            return "color: green; font-size: 16px; text-align: center;"
        return "font-size: 16px; text-align: center;"

    st.markdown("### 📊 Frequenza storica con evidenziazione")
    styled_df = df_freq.style.apply(lambda row: [colore_numero(row)] * len(row), axis=1)
    st.dataframe(styled_df)
