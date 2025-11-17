import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==============================================================================
# ⚙️ KONFIGURASI APLIKASI
# ==============================================================================
st.set_page_config(
    page_title="Kalkulator Rights Issue",
    page_icon="💸",
    layout="centered" 
)

# =id="app-container">
def local_css():
    st.markdown("""
    <style>
    /* ----------------------------------------------------------------- */
    /* [PERBAIKAN] FORCE DARK THEME UNTUK KETERBACAAN MAKSIMAL
    /* ----------------------------------------------------------------- */
    
    /* Background utama aplikasi */
    body, [data-testid="stAppViewContainer"] {
        background-color: #0E1117; /* Streamlit dark bg */
        color: #FAFAFA; /* Default text putih */
    }
    
    /* Main content padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Sidebar dark */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E; /* Latar belakang sidebar sedikit lebih terang */
        padding: 15px;
        color: #FAFAFA; /* Atur default text color jadi putih */
    }
    
    [data-testid="stSidebar"] h2 {
        color: #00AFFF; /* Biru terang untuk judul sidebar */
        border-bottom: 2px solid #262730;
        padding-bottom: 10px;
    }
    
    /* Target spesifik label input dan header form di sidebar */
    [data-testid="stSidebar"] .stForm h3, 
    [data-testid="stSidebar"] .stForm label,
    [data-testid="stSidebar"] .stMarkdown {
        color: #FAFAFA !important; /* Pakai !important untuk memaksa */
    }
    
    /* Card styling untuk hasil */
    .result-card {
        background-color: #262730; /* Streamlit card dark */
        border-radius: 10px; padding: 25px;
        margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #31333F; /* Border gelap */
    }
    
    .result-card h3 {
        color: #FAFAFA; /* Teks header card putih */
        margin-top: 0; margin-bottom: 15px;
        border-bottom: 2px solid #31333F;
        padding-bottom: 10px;
    }
    
    .result-card p, .result-card ul li {
         color: #FAFAFA; /* Teks list putih */
    }

    /* Styling untuk st.metric */
    [data-testid="stMetric"] {
        background-color: #1E1E1E; /* Background metric lebih gelap */
        border-radius: 8px; padding: 15px;
        border: 1px solid #31333F;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 16px; color: #AAAAAA; /* Label metric abu-abu muda */
    }
    
    [data-testid="stMetricValue"] {
        font-size: 32px; font-weight: 600;
        color: #00AFFF; /* Nilai metric biru terang */
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 18px; font-weight: 600;
    }

    /* Tombol sidebar */
    .stButton>button {
        background-color: #007AFF; color: white;
        font-weight: bold; border-radius: 8px;
        border: none; padding: 10px 20px;
        width: 100%; transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 2px 5px rgba(0,122,255,0.3);
    }
    
    .stAlert { color: #333; }

    /* [BARU] Styling untuk PNL di card */
    .pnl-positive { color: #28A745; font-weight: bold; }
    .pnl-negative { color: #FF4B4B; font-weight: bold; }
    .new-avg-price { color: #00AFFF; font-weight: bold; font-size: 1.1em; }

    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# 🧮 FUNGSI KALKULASI INTI
# ==============================================================================

def calculate_theoretical_price(P_market, N_old, P_exercise, N_new):
    """Menghitung Harga Teori (Ex-Date)."""
    if (N_old + N_new) == 0:
        return 0, 0, 0
        
    P_teori = ((N_old * P_market) + (N_new * P_exercise)) / (N_old + N_new)
    Nilai_HMETD = P_teori - P_exercise
    
    if P_market == 0:
        Dilution_pct = 0
    else:
        Dilution_pct = (P_market - P_teori) / P_market * 100
        
    return P_teori, Nilai_HMETD, Dilution_pct

# [BARU] Fungsi helper untuk PNL
def format_pnl(pnl_value):
    """Memberi style PNL (Positif/Negatif) untuk HTML."""
    if pnl_value > 0:
        return f'<span class="pnl-positive">Rp {pnl_value:,.0f} (Profit)</span>'
    elif pnl_value < 0:
        return f'<span class="pnl-negative">Rp {pnl_value:,.0f} (Loss)</span>'
    else:
        return f'<span>Rp {pnl_value:,.0f} (BEP)</span>'

# ==============================================================================
#  sidebar  INPUT DARI USER
# ==============================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Download_Indicator_Arrow.svg/2048px-Download_Indicator_Arrow.svg.png", width=50)
st.sidebar.title("Kalkulator Rights Issue")
st.sidebar.markdown("Masukkan data prospektus untuk menganalisis apakah *rights issue* ini menguntungkan.")

with st.sidebar.form("ri_form"):
    st.header("1. Data Pasar & Rasio")
    
    P_market = st.number_input(
        "Harga Pasar Saat Ini (Rp)",
        min_value=0, value=1000, step=50,
        help="Harga saham di pasar sebelum tanggal Cum-Date."
    )
    
    st.markdown("---")
    st.markdown("**Rasio Rights Issue (Contoh: 10:3)**")
    col_a, col_b = st.columns(2)
    N_old = col_a.number_input("Saham Lama", min_value=1, value=10)
    N_new = col_b.number_input("Hak Tebus (Baru)", min_value=1, value=3)
    st.markdown("---")

    st.header("2. Data Rights Issue")
    P_exercise = st.number_input(
        "Harga Tebus / Exercise (Rp)",
        min_value=0, value=500, step=50,
        help="Harga untuk menebus 1 lembar saham baru."
    )
    
    st.header("3. (Opsional) Posisi Anda")
    My_Shares = st.number_input(
        "Jumlah Saham Anda Saat Ini",
        min_value=0, value=1000, step=100,
        help="Jumlah saham yang Anda pegang (untuk simulasi dilusi)."
    )
    
    # [PERUBAHAN] Input baru untuk Harga Beli Rata-Rata
    My_Avg_Price = st.number_input(
        "Harga Beli Rata-Rata Anda (Rp)",
        min_value=0.0, value=float(P_market), step=50.0, format="%.2f",
        help="Harga modal (average price) Anda saat ini. Default = Harga Pasar."
    )
    
    submit_button = st.form_submit_button("Hitung Analisis 🧮")

# ==============================================================================
# 📊 TAMPILAN UTAMA & HASIL
# ==============================================================================
st.title("💸 Analisis Kelayakan Rights Issue")
st.markdown(f"Menganalisis skenario **{N_old} : {N_new}** dengan harga tebus **Rp {P_exercise:,.0f}** dan harga pasar **Rp {P_market:,.0f}**.")

if submit_button:
    # Lakukan kalkulasi
    P_teori, Nilai_HMETD, Dilution_pct = calculate_theoretical_price(P_market, N_old, P_exercise, N_new)

    st.markdown("---")
    
    # --- Tampilan Metrik Utama ---
    st.markdown("### 📊 Hasil Kalkulasi Utama")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Harga Teori (Ex-Date)", f"Rp {P_teori:,.2f}", f"{Dilution_pct:,.2f}% vs Pasar", delta_color="inverse")
    col2.metric("Nilai 1 Hak Tebus (HMETD)", f"Rp {Nilai_HMETD:,.2f}", "Wajib Positif")
    col3.metric("Potensi Dilusi (jika tidak tebus)", f"{Dilution_pct:,.2f}%")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Tampilan Analisis Fund Manager ---
    st.markdown("### 🧠 Analisis Fund Manager")
    
    if Nilai_HMETD < 0:
        st.error(
            f"**ANALISIS: MERUGIKAN! ❌** \n\n"
            f"Harga Tebus (Rp {P_exercise:,.0f}) **lebih mahal** daripada Harga Teori (Rp {P_teori:,.2f}). "
            "Ini adalah skenario yang sangat langka dan merugikan."
        )
    else:
        st.success(
            f"**ANALISIS: WAJIB DITEBUS! ✅** \n\n"
            f"Setiap 1 hak tebus (HMETD) Anda memiliki nilai intrinsik **Rp {Nilai_HMETD:,.2f}**. "
            "Anda 'diuntungkan' karena bisa membeli saham di harga tebus (Rp {P_exercise:,.0f}) yang jauh lebih murah daripada harga teorinya (Rp {P_teori:,.2f})."
        )
        st.info(
            f"**STRATEGI:** Anda **wajib menebus** semua hak Anda. Jika Anda tidak menebus, "
            f"saham Anda akan terdilusi dan nilainya akan turun sebesar **{Dilution_pct:,.2f}%** "
            f"secara cuma-cuma (rugi kertas) saat *ex-date*."
        )

    st.markdown("---")
    
    # --- [PERUBAHAN] Tampilan Simulasi (dengan PNL) ---
    if My_Shares > 0 and My_Avg_Price > 0: # Hanya tampilkan jika harga beli diisi
        st.markdown("### 💰 Simulasi PNL Posisi Anda")
        
        # --- Hitung kalkulasi PNL ---
        My_Rights = (My_Shares / N_old) * N_new
        Cost_to_Exercise = My_Rights * P_exercise
        
        # Kalkulasi SEBELUM RI
        Cost_Basis_Before = My_Shares * My_Avg_Price
        Value_Before = My_Shares * P_market
        PNL_Before = Value_Before - Cost_Basis_Before
        
        # Kalkulasi Skenario 1 (TIDAK Menebus)
        Value_After_No_Exercise = My_Shares * P_teori
        PNL_After_No_Exercise = Value_After_No_Exercise - Cost_Basis_Before
        Loss_No_Exercise = Value_Before - Value_After_No_Exercise # Ini kerugian dilusi
        
        # Kalkulasi Skenario 2 (MENEBUS)
        Total_Shares_After = My_Shares + My_Rights
        Cost_Basis_After = Cost_Basis_Before + Cost_to_Exercise
        New_Avg_Price = Cost_Basis_After / Total_Shares_After # <- HARGA RATA-RATA BARU
        Value_After_Exercise = Total_Shares_After * P_teori
        PNL_After_Exercise = Value_After_Exercise - Cost_Basis_After
        
        st.markdown(f"Anda memiliki **{My_Shares:,.0f}** lembar saham dengan harga beli rata-rata **Rp {My_Avg_Price:,.2f}**. Anda mendapat **{My_Rights:,.0f}** hak tebus.")
        
        sim_col1, sim_col2 = st.columns(2)
        
        with sim_col1:
            st.markdown(
                f"""
                <div class="result-card" style="border-left: 5px solid #D93025;">
                <h3>Skenario 1: TIDAK Menebus</h3>
                <p>Anda membiarkan hak Anda hangus.</p>
                <ul>
                    <li>Modal Awal: <strong>Rp {Cost_Basis_Before:,.0f}</strong></li>
                    <li>PNL Awal (vs Pasar): {format_pnl(PNL_Before)}</li>
                    <hr style="border-top: 1px dashed #31333F; margin: 10px 0;">
                    <li>Nilai Aset (Ex-Date): <strong>Rp {Value_After_No_Exercise:,.0f}</strong></li>
                    <li>PNL Baru (vs Teori): {format_pnl(PNL_After_No_Exercise)}</li>
                </ul>
                <h4 style="color: #FF4B4B;">Kerugian Dilusi: Rp {Loss_No_Exercise:,.0f}</h4>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with sim_col2:
            st.markdown(
                f"""
                <div class="result-card" style="border-left: 5px solid #1E8E3E;">
                <h3>Skenario 2: MENEBUS Semua</h3>
                <p>Anda menebus semua hak (butuh dana Rp {Cost_to_Exercise:,.0f}).</p>
                <ul>
                    <li>Total Modal Baru: <strong>Rp {Cost_Basis_After:,.0f}</strong></li>
                    <li>Total Saham Baru: <strong>{Total_Shares_After:,.0f} lembar</strong></li>
                    <hr style="border-top: 1px dashed #31333F; margin: 10px 0;">
                    <li><span class="new-avg-price">Avg. Price BARU: <strong>Rp {New_Avg_Price:,.2f}</strong></span></li>
                    <li>Nilai Aset (Ex-Date): <strong>Rp {Value_After_Exercise:,.0f}</strong></li>
                    <li>PNL Baru (vs Teori): {format_pnl(PNL_After_Exercise)}</li>
                </ul>
                <h4 style="color: #28A745;">PNL & Aset Anda Terlindungi</h4>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    elif My_Shares > 0 and My_Avg_Price == 0:
         st.warning("Silakan masukkan 'Harga Beli Rata-Rata Anda' di sidebar untuk melihat simulasi PNL.", icon="⚠️")


else:
    st.info("Masukkan parameter *rights issue* di *sidebar* kiri dan klik 'Hitung Analisis'.")

st.markdown("---")
st.markdown("**Disclaimer:** Kalkulator ini hanya menghitung harga teori berdasarkan prospektus. Harga pasar riil di *ex-date* dapat berbeda karena sentimen pasar.")
