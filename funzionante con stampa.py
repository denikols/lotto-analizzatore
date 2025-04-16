import streamlit as st
import pandas as pd
from collections import Counter
from datetime import timedelta
import base64

st.set_page_config(page_title="Sistema Lotto", layout="centered")

# CSS semplificato per la stampa
st.markdown("""
<style>
@media print {
    .stApp header, .stApp footer, .stSidebar, button, .stToolbar, .stAnnotated, [data-testid="stFileUploadDropzone"] {
        display: none !important;
    }
    
    /* Stile per la stampa */
    body {
        font-size: 12px !important;
    }
    
    h1, h2, h3 {
        margin-top: 10px !important;
        margin-bottom: 5px !important;
    }
    
    /* Assicura che il contenuto sia visibile */
    .element-container, .stAlert, .stDataFrame, .stMarkdown {
        max-width: 100% !important;
        width: 100% !important;
        padding: 0 !important;
        display: block !important;
    }
}

/* Stile per il pulsante personalizzato */
.download-button {
    padding: 0.25rem 0.75rem;
    background-color: #4CAF50;
    color: white !important;
    text-decoration: none;
    border-radius: 4px;
    cursor: pointer;
    display: inline-block;
    margin: 10px 0;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Funzione per generare link di download HTML
def create_download_link(content, filename, link_text):
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}" class="download-button">{link_text}</a>'
    return href

st.title("🎯 Sistema Lotto - Analisi Completa per Ruota con Numeri Spia")

uploaded_file = st.file_uploader("Carica il file CSV delle estrazioni", type="csv")

if uploaded_file:
    # Leggi il file CSV, assumendo che le prime 3 righe sono intestazioni
    df = pd.read_csv(uploaded_file, skiprows=3)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    ruote = ["Bari", "Cagliari", "Firenze", "Genova", "Milano",
             "Napoli", "Palermo", "Roma", "Torino", "Venezia", "Nazionale"]

    st.success("File caricato correttamente!")

    col1, col2 = st.columns(2)
    with col1:
        ruota_input = st.selectbox("Scegli la ruota per calcolo base", ruote)
    with col2:
        data_estrazione = st.date_input("Data estrazione", value=df["Data"].max().date())

    st.subheader("⚙️ Impostazioni Analisi Numeri Spia")
    numero_spia_input = st.number_input("Inserisci il numero spia da analizzare (1-90)", min_value=1, max_value=90, value=10)
    finestra_analisi_spia = st.slider("Finestra di analisi per numeri spia (ultime N estrazioni)", min_value=50, max_value=1000, value=300, step=50)

    def get_numeri_estrazione(data, ruota):
        row = df[df["Data"] == pd.Timestamp(data)]
        if row.empty:
            return []
        cols = [ruota, f"{ruota}.1", f"{ruota}.2", f"{ruota}.3", f"{ruota}.4"]
        numeri = row[cols].iloc[0].tolist()
        return [int(n) for n in numeri if pd.notnull(n)]

    def get_gruppo_numeri(numeri):
        gruppo = set()
        successivi = set()
        for num in numeri:
            successivi.update([num - 1 if num > 1 else 90, num + 1 if num < 90 else 1])
        return sorted(numeri), sorted(successivi)

    def calcola_statistiche_ruota(df, numeri, max_data):
        punteggi = []
        for ruota in ruote:
            cols = [ruota, f"{ruota}.1", f"{ruota}.2", f"{ruota}.3", f"{ruota}.4"]
            numeri_ruota = df[cols].apply(pd.to_numeric, errors="coerce")

            freq = numeri_ruota.apply(pd.Series.value_counts).sum(axis=1).reindex(numeri, fill_value=0).sum()

            ritardi = []
            for num in numeri:
                trovato = False
                for i, row in df.sort_values("Data", ascending=False).iterrows():
                    estratti = [row[c] for c in cols if pd.notnull(row[c])]
                    if num in estratti:
                        ritardi.append((max_data - row["Data"]).days)
                        trovato = True
                        break
                if not trovato:
                    ritardi.append((max_data - df["Data"].min()).days)
            rit_medio = sum(ritardi) / len(ritardi)

            recenti = df[df["Data"] > max_data - timedelta(days=60)].sort_values("Data", ascending=False).head(10)
            ripetuti = 0
            for _, row in recenti.iterrows():
                estratti = [row[c] for c in cols if pd.notnull(row[c])]
                ripetuti += len(set(estratti) & set(numeri))

            punteggi.append({
                "Ruota": ruota,
                "Frequenze": freq,
                "Ritardo medio": round(rit_medio, 1),
                "Ripetizioni recenti": ripetuti,
                "Punteggio": freq * 0.4 + rit_medio * 0.2 + ripetuti * 1.5
            })
        return pd.DataFrame(punteggi).sort_values("Punteggio", ascending=False)

    def suggerisci_per_ruota(df, ruota, num_top=5):
        """Suggerisce i migliori numeri da giocare per una ruota specifica."""
        cols = [ruota, f"{ruota}.1", f"{ruota}.2", f"{ruota}.3", f"{ruota}.4"]
        
        # Creiamo una lista di tutti i numeri estratti sulla ruota
        tutti_numeri = []
        for _, row in df.iterrows():
            estratti = [row[c] for c in cols if pd.notnull(row[c])]
            tutti_numeri.extend([int(n) for n in estratti])
        
        # Calcola frequenza
        conteggio = Counter(tutti_numeri)
        
        # Calcola ritardi
        ritardi = {}
        for num in range(1, 91):
            ultimo_estratto = None
            for _, row in df.sort_values("Data", ascending=False).iterrows():
                estratti = [int(row[c]) for c in cols if pd.notnull(row[c])]
                if num in estratti:
                    ultimo_estratto = row["Data"]
                    break
            
            if ultimo_estratto:
                ritardi[num] = (df["Data"].max() - ultimo_estratto).days
            else:
                ritardi[num] = 999  # Se mai estratto, alto ritardo

        # Calcola punteggio combinato (frequenza * 0.4 + ritardo * 0.6)
        punteggi = {}
        for num in range(1, 91):
            freq = conteggio.get(num, 0)
            rit = ritardi.get(num, 999)
            
            # Normalizza la frequenza (più è alta, meglio è)
            freq_norm = freq / max(conteggio.values()) if conteggio else 0
            
            # Normalizza il ritardo (più è alto, meglio è - perché è più probabile che esca)
            rit_norm = rit / max(ritardi.values()) if ritardi else 0
            
            punteggi[num] = freq_norm * 0.4 + rit_norm * 0.6
        
        # Ordina numeri per punteggio e restituisci i top
        numeri_ordinati = sorted(punteggi.items(), key=lambda x: x[1], reverse=True)
        return numeri_ordinati[:num_top]

    def analizza_numeri_spia(df, numero_spia, ruota, finestra):
        df_ruota = df[[ruota, f"{ruota}.1", f"{ruota}.2", f"{ruota}.3", f"{ruota}.4", "Data"]].dropna()
        df_ruota_sorted = df_ruota.sort_values(by="Data", ascending=False).head(finestra).reset_index(drop=True)

        numeri_successivi = Counter()
        for i in range(len(df_ruota_sorted) - 1):
            estrazione_corrente = [int(x) for x in df_ruota_sorted.iloc[i][0:5].tolist()]
            estrazione_successiva = [int(x) for x in df_ruota_sorted.iloc[i + 1][0:5].tolist()]

            if numero_spia in estrazione_corrente:
                numeri_successivi.update(estrazione_successiva)

        totale_uscite_spia = sum(1 for index, row in df_ruota_sorted.iterrows() if numero_spia in [int(x) for x in row[0:5].tolist()])
        if totale_uscite_spia > 0:
            probabilita_successiva = {num: count / totale_uscite_spia for num, count in numeri_successivi.items()}
            probabilita_ordinata = sorted(probabilita_successiva.items(), key=lambda item: item[1], reverse=True)[:5]  # Limita a 5 numeri
            return probabilita_ordinata
        else:
            return []

    # Contenitore principale per la visualizzazione dei risultati
    results_container = st.container()
    
    with results_container:
        st.subheader("🔮 Numeri Suggeriti per i Prossimi Turni (massimo 5)")
        risultati_spia = analizza_numeri_spia(df, numero_spia_input, ruota_input, finestra_analisi_spia)

        if risultati_spia:
            numeri_suggeriti = [f"**{int(num)}** ({probabilita:.2%})" for num, probabilita in risultati_spia]
            st.markdown(f"<p style='font-size:16px; color:green;'>Basati sull'analisi del numero spia <b>{numero_spia_input}</b> sulla ruota di <b>{ruota_input}</b>, i numeri con maggiore probabilità di uscire nei prossimi turni sono: <br> {', '.join(numeri_suggeriti)}</p>", unsafe_allow_html=True)
        else:
            st.info(f"L'analisi del numero spia {numero_spia_input} sulla ruota di {ruota_input} non ha prodotto suggerimenti significativi (il numero spia potrebbe non essere uscito abbastanza frequentemente nella finestra analizzata).")

        if 'df' in locals(): # Verifica se il DataFrame è stato creato
            numeri_base = get_numeri_estrazione(data_estrazione, ruota_input)
            diretti, successivi = get_gruppo_numeri(numeri_base)
            numeri_finali = sorted(set(diretti + successivi))

            st.markdown(f"### ✅ Analisi dei numeri: {', '.join(map(str, numeri_finali))}")

            df_stat = calcola_statistiche_ruota(df, numeri_finali, df["Data"].max())
            st.subheader("📊 Statistiche per Ruota (Numeri Analizzati)")
            st.dataframe(df_stat)
            
            # NUOVA SEZIONE: Suggerimenti dei numeri migliori per le ruote con punteggio più alto
            st.subheader("🎲 Numeri Consigliati per Ciascuna Ruota")
            
            # Prendi le prime 5 ruote con punteggio più alto
            top_ruote = df_stat.head(5)["Ruota"].tolist()
            
            # Versione con tabs per la visualizzazione normale
            tabs = st.tabs([f"Ruota {ruota}" for ruota in top_ruote])
            
            for i, ruota in enumerate(top_ruote):
                with tabs[i]:
                    st.markdown(f"#### 🎯 I migliori numeri da giocare sulla ruota di {ruota}")
                    migliori_numeri = suggerisci_per_ruota(df, ruota, num_top=10)
                    
                    # Crea due colonne
                    col1, col2 = st.columns(2)
                    
                    # Nella prima colonna, mostra i numeri
                    with col1:
                        numeri_html = []
                        for num, score in migliori_numeri:
                            # Colora di verde se è nei numeri originali
                            if num in numeri_finali:
                                numeri_html.append(f"<span style='color:green; font-weight:bold;'>{num}</span> ({score:.2f})")
                            else:
                                numeri_html.append(f"{num} ({score:.2f})")
                        
                        st.markdown(", ".join(numeri_html), unsafe_allow_html=True)
                    
                    # Nella seconda colonna, mostra una leggenda
                    with col2:
                        st.markdown("""
                        **Legenda**:
                        - <span style='color:green; font-weight:bold;'>Verde</span>: Numeri presenti nell'analisi iniziale
                        - Punteggio: Combinazione di frequenza e ritardo
                        """, unsafe_allow_html=True)
                    
                    # Mostra anche l'ultimo turno in cui sono usciti
                    st.markdown("#### Ultima estrazione su questa ruota:")
                    ultima_estrazione = df.sort_values("Data", ascending=False).iloc[0]
                    data_ultima = ultima_estrazione["Data"].date()
                    numeri_ultima = [int(ultima_estrazione[f"{ruota}{'' if i==0 else '.'+str(i)}"]) for i in range(5) if pd.notnull(ultima_estrazione[f"{ruota}{'' if i==0 else '.'+str(i)}"]) ]
                    
                    st.markdown(f"Data: **{data_ultima}** - Numeri estratti: **{', '.join(map(str, numeri_ultima))}**")

            st.markdown("### 🔁 Ripetizioni nei 5 turni successivi (con ambi e terni)")
            st.markdown(f"<p style='font-size:16px; margin-top:-8px; color:black;'>Estratti base: <b>{', '.join(map(str, diretti))}</b></p>", unsafe_allow_html=True)

            prossime = df[df["Data"] > pd.Timestamp(data_estrazione)].sort_values("Data").head(5)
            col_estrazioni, col_legenda = st.columns([4, 1])

            with col_estrazioni:
                for _, row in prossime.iterrows():
                    estratti = [row[f"{ruota_input}"], row[f"{ruota_input}.1"], row[f"{ruota_input}.2"], row[f"{ruota_input}.3"], row[f"{ruota_input}.4"]]
                    estratti = [int(n) for n in estratti if pd.notnull(n)]
                    colorati = []
                    count_estratti = 0
                    for num in estratti:
                        if num in diretti:
                            colorati.append(f"<span style='color:green'><b>{num}</b></span>")
                        elif num in successivi:
                            colorati.append(f"<span style='color:orange'><b>{num}</b></span>")
                        else:
                            colorati.append(f"<span style='color:black'>{num}</span>")
                        if num in numeri_finali:
                            count_estratti += 1
                    simbolo = ""
                    if count_estratti >= 3:
                        simbolo = "<span style='color:red; font-size:22px'><b>T</b></span>"
                    elif count_estratti == 2:
                        simbolo = "<span style='color:red; font-size:22px'><b>A</b></span>"
                    st.markdown(f"🗓️ {row['Data'].date()} → Usciti: " + ", ".join(colorati) + f" {simbolo}", unsafe_allow_html=True)

            with col_legenda:
                st.markdown("""
        <span style='color:green'><b>Verde</b></span>: Estratti base<br>
        <span style='color:orange'><b>Arancione</b></span>: Precedenti/Successivi<br>
        <span style='color:red; font-size:18px'><b>A</b></span>: Ambo<br>
        <span style='color:red; font-size:18px'><b>T</b></span>: Terno
                """, unsafe_allow_html=True)
            
            # Crea report stampabile in formato HTML
            report_html = f"""
            <html>
            <head>
                <title>Report Lotto - {pd.Timestamp.now().strftime("%d/%m/%Y")}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    table, th, td {{ border: 1px solid #ddd; }}
                    th, td {{ padding: 8px; text-align: left; }}
                    .green {{ color: green; font-weight: bold; }}
                    .orange {{ color: orange; font-weight: bold; }}
                    .red {{ color: red; font-weight: bold; }}
                    .header {{ text-align: center; margin-bottom: 20px; }}
                    .footer {{ text-align: center; margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Report Analisi Lotto</h1>
                    <p>Data generazione: {pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")}</p>
                    <hr>
                </div>
                
                <h2>🔮 Numeri Suggeriti per i Prossimi Turni</h2>
                <p>Basati sull'analisi del numero spia <b>{numero_spia_input}</b> sulla ruota di <b>{ruota_input}</b></p>
                """
            
            # Aggiungi risultati dell'analisi spia
            if risultati_spia:
                report_html += "<p>I numeri con maggiore probabilità di uscire sono:</p><ul>"
                for num, prob in risultati_spia:
                    report_html += f"<li><b>{num}</b> ({prob:.2%})</li>"
                report_html += "</ul>"
            
            # Aggiungi info sui numeri analizzati
            report_html += f"""
                <h2>✅ Analisi dei numeri: {', '.join(map(str, numeri_finali))}</h2>
                <p>Estratti base: <b>{', '.join(map(str, diretti))}</b></p>
                <p>Numeri successivi/precedenti: <b>{', '.join(map(str, successivi))}</b></p>
                
                <h2>📊 Statistiche per Ruota</h2>
                <table>
                    <tr>
                        <th>Ruota</th>
                        <th>Frequenze</th>
                        <th>Ritardo medio</th>
                        <th>Ripetizioni recenti</th>
                        <th>Punteggio</th>
                    </tr>
            """
            
            # Aggiungi dati della tabella statistiche
            for _, row in df_stat.iterrows():
                report_html += f"""
                    <tr>
                        <td>{row['Ruota']}</td>
                        <td>{row['Frequenze']}</td>
                        <td>{row['Ritardo medio']}</td>
                        <td>{row['Ripetizioni recenti']}</td>
                        <td><b>{row['Punteggio']:.2f}</b></td>
                    </tr>
                """
            
            report_html += "</table>"
            
            # Aggiungi numeri consigliati per le top ruote
            report_html += "<h2>🎲 Numeri Consigliati per le Ruote Principali</h2>"
            
            for ruota in top_ruote:
                report_html += f"<h3>Ruota di {ruota}</h3>"
                migliori_numeri = suggerisci_per_ruota(df, ruota, num_top=10)
                
                report_html += "<p>Numeri consigliati: "
                numeri_formattati = []
                for num, score in migliori_numeri:
                    if num in numeri_finali:
                        numeri_formattati.append(f"<span class='green'>{num}</span> ({score:.2f})")
                    else:
                        numeri_formattati.append(f"{num} ({score:.2f})")
                
                report_html += ", ".join(numeri_formattati) + "</p>"
                
                # Aggiungi ultima estrazione
                ultima_estrazione = df.sort_values("Data", ascending=False).iloc[0]
                data_ultima = ultima_estrazione["Data"].date()
                numeri_ultima = [int(ultima_estrazione[f"{ruota}{'' if i==0 else '.'+str(i)}"]) for i in range(5) if pd.notnull(ultima_estrazione[f"{ruota}{'' if i==0 else '.'+str(i)}"]) ]
                
                report_html += f"<p>Ultima estrazione ({data_ultima}): <b>{', '.join(map(str, numeri_ultima))}</b></p>"
            
            # Aggiungi sezione ripetizioni
            report_html += """
                <h2>🔁 Ripetizioni nei 5 turni successivi</h2>
                <p><span class='green'>Verde</span>: Estratti base, 
                <span class='orange'>Arancione</span>: Numeri successivi/precedenti, 
                <span class='red'>A</span>: Ambo, 
                <span class='red'>T</span>: Terno</p>
                <table>
                    <tr><th>Data</th><th>Numeri estratti</th><th>Note</th></tr>
            """
            
            for _, row in prossime.iterrows():
                estratti = [row[f"{ruota_input}"], row[f"{ruota_input}.1"], row[f"{ruota_input}.2"], row[f"{ruota_input}.3"], row[f"{ruota_input}.4"]]
                estratti = [int(n) for n in estratti if pd.notnull(n)]
                colorati = []
                count_estratti = 0
                
                for num in estratti:
                    if num in diretti:
                        colorati.append(f"<span class='green'>{num}</span>")
                    elif num in successivi:
                        colorati.append(f"<span class='orange'>{num}</span>")
                    else:
                        colorati.append(f"{num}")
                    if num in numeri_finali:
                        count_estratti += 1
                
                simbolo = ""
                if count_estratti >= 3:
                    simbolo = "<span class='red'>T</span>"
                elif count_estratti == 2:
                    simbolo = "<span class='red'>A</span>"
                
                report_html += f"<tr><td>{row['Data'].date()}</td><td>{', '.join(colorati)}</td><td>{simbolo}</td></tr>"
            
            report_html += """
                </table>
                
                <div class="footer">
                    <p>Sistema Lotto - Analisi generata automaticamente</p>
                </div>
            </body>
            </html>
            """
            
            # Mostra pulsanti per stampa e download
            st.markdown("## 🖨️ Stampa e Salvataggio")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(create_download_link(
                    report_html, 
                    f"report_lotto_{pd.Timestamp.now().strftime('%Y%m%d')}.html",
                    "📥 Scarica Report HTML"
                ), unsafe_allow_html=True)
                
            with col2:
                # Pulsante per stampare direttamente dalla pagina
                st.markdown("""
                <a href="#" onclick="window.print()" class="download-button">🖨️ Stampa questa pagina</a>
                """, unsafe_allow_html=True)
            
            st.info("💡 Per stampare il report completo:\n"
                    "1. Clicca su 'Stampa questa pagina' o usa CTRL+P (⌘+P su Mac)\n"
                    "2. Oppure scarica il report HTML e aprilo nel tuo browser")