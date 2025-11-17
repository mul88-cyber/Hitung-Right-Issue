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
    layout="centered" # Layout terpusat lebih cocok untuk kalkulator
)

# =id="app-container">
def local_css():
    st.markdown("""
    <style>
    /* Styling untuk app container */
    [data-testid="stAppViewContainer"] {
        background-color: #F0F2F6; /* Latar belakang abu-abu muda */
    }
    
    /* Styling untuk main content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Card styling untuk hasil */
    .result-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0;
    }
    
    .result-card h3 {
        color: #1a1a1a;
        margin-top: 0;
        margin-bottom: 15px;
        border-bottom: 2px solid #F0F2F6;
        padding-bottom: 10px;
    }

    /* Styling untuk st.metric */
    [data-testid="stMetric"] {
        background-color: #FAFAFA;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #E0E0E0;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 16px;
        color: #555;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 600;
        color: #007AFF; /* Biru */
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 18px;
        font-weight: 600;
    }

    /* Styling sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        padding: 15px;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #007AFF;
        border-bottom: 2px solid #F0F2F6;
        padding-bottom: 10px;
    }
    
    .stButton>button {
        background-color: #007AFF;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 2px 5px rgba(0,122,255,0.3);
    }

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
        
    # Rumus Harga Teori
    # (Total Nilai Saham Lama + Total Dana RI) / (Total Saham Baru)
    P_teori = ((N_old * P_market) + (N_new * P_exercise)) / (N_old + N_new)
    
    # Nilai 1 HMETD (Hak Tebus)
    # Selisih antara harga teori dengan harga tebus
    Nilai_HMETD = P_teori - P_exercise
    
    # Potensi Dilusi (jika tidak exercise)
    # Seberapa besar harga saham lama turun
    if P_market == 0:
        Dilution_pct = 0
    else:
        Dilution_pct = (P_market - P_teori) / P_market * 100
        
    return P_teori, Nilai_HMETD, Dilution_pct

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
        min_value=0,
        value=1000,
        step=50,
        help="Harga saham di pasar sebelum tanggal Cum-Date."
    )
    
    st.markdown("---")
    st.markdown("**Rasio Rights Issue (Contoh: 10:3)**")
    col_a, col_b = st.columns(2)
    N_old = col_a.number_input(
        "Saham Lama",
        min_value=1,
        value=10,
        help="Jumlah saham lama yang dimiliki."
    )
    N_new = col_b.number_input(
        "Hak Tebus (Baru)",
        min_value=1,
        value=3,
        help="Jumlah hak tebus yang didapat."
    )
    st.markdown("---")

    st.header("2. Data Rights Issue")
    P_exercise = st.number_input(
        "Harga Tebus / Exercise (Rp)",
        min_value=0,
        value=500,
        step=50,
        help="Harga untuk menebus 1 lembar saham baru."
    )
    
    st.header("3. (Opsional) Kepemilikan Anda")
    My_Shares = st.number_input(
        "Jumlah Saham Anda Saat Ini",
        min_value=0,
        value=1000,
        step=100,
        help="Jumlah saham yang Anda pegang (untuk simulasi dilusi)."
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
    col1.metric(
        "Harga Teori (Ex-Date)",
        f"Rp {P_teori:,.2f}",
        f"{Dilution_pct:,.2f}% vs Pasar",
        delta_color="inverse" # Merah karena harga turun (dilusi)
    )
    
    col2.metric(
        "Nilai 1 Hak Tebus (HMETD)",
        f"Rp {Nilai_HMETD:,.2f}",
        "Wajib Positif"
    )
    
    col3.metric(
        "Potensi Dilusi (jika tidak tebus)",
        f"{Dilution_pct:,.2f}%"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Tampilan Analisis Fund Manager ---
    st.markdown("### 🧠 Analisis Fund Manager")
    
    if Nilai_HMETD < 0:
        # Skenario Aneh (Harga Tebus > Harga Teori)
        st.error(
            f"**ANALISIS: MERUGIKAN! ❌** \n\n"
            f"Harga Tebus (Rp {P_exercise:,.0f}) **lebih mahal** daripada Harga Teori (Rp {P_teori:,.2f}). "
            "Ini adalah skenario yang sangat langka dan merugikan. Tidak ada insentif untuk menebus saham ini."
        )
    else:
        # Skenario Normal (Harga Tebus < Harga Teori)
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
    
    # --- Tampilan Simulasi (jika diisi) ---
    if My_Shares > 0:
        st.markdown("### 💰 Simulasi Kepemilikan Anda")
        
        # Hitung simulasi
        My_Rights = (My_Shares / N_old) * N_new
        Cost_to_Exercise = My_Rights * P_exercise
        
        Value_Before = My_Shares * P_market
        Value_After_No_Exercise = My_Shares * P_teori
        Loss_No_Exercise = Value_Before - Value_After_No_Exercise
        
        Total_Shares_After = My_Shares + My_Rights
        Value_After_Exercise = Total_Shares_After * P_teori
        Total_Cost = Value_Before + Cost_to_Exercise # Total modal yg dikeluarkan
        
        st.markdown(f"Anda memiliki **{My_Shares:,.0f}** lembar saham, sehingga Anda akan mendapat **{My_Rights:,.0f}** hak tebus (HMETD).")
        
        sim_col1, sim_col2 = st.columns(2)
        
        with sim_col1:
            st.markdown(
                f"""
                <div class="result-card" style="border-left: 5px solid #D93025;">
                <h3>Skenario 1: TIDAK Menebus</h3>
                <p>Anda tidak melakukan apa-apa dan membiarkan hak Anda hangus.</p>
                <ul>
                    <li>Nilai Aset Awal: <strong>Rp {Value_Before:,.0f}</strong></li>
                    <li>Nilai Aset (Ex-Date): <strong>Rp {Value_After_No_Exercise:,.0f}</strong></li>
                </ul>
                <h4 style="color: #D93025;">Kerugian Dilusi: Rp {Loss_No_Exercise:,.0f}</h4>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with sim_col2:
            st.markdown(
                f"""
                <div class="result-card" style="border-left: 5px solid #1E8E3E;">
                <h3>Skenario 2: MENEBUS Semua</h3>
                <p>Anda mengeluarkan dana untuk menebus semua hak.</p>
                <ul>
                    <li>Dana Tambahan (Tebus): <strong>Rp {Cost_to_Exercise:,.0f}</strong></li>
                    <li>Nilai Aset (Ex-Date): <strong>Rp {Value_After_Exercise:,.0f}</strong></li>
                </ul>
                <h4 style="color: #1E8E3E;">Total Aset Anda Terjaga</h4>
                </div>
                """,
                unsafe_allow_html=True
            )

else:
    st.info("Masukkan parameter *rights issue* di *sidebar* kiri dan klik 'Hitung Analisis'.")

st.markdown("---")
st.markdown("**Disclaimer:** Kalkulator ini hanya menghitung harga teori berdasarkan prospektus. Harga pasar riil di *ex-date* dapat berbeda karena sentimen pasar.")
