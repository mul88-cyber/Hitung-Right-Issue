import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import math

# ==============================================================================
# ⚙️ KONFIGURASI APLIKASI
# ==============================================================================
st.set_page_config(
    page_title="Kalkulator & Dashboard Rights Issue",
    page_icon="💸",
    layout="wide" # Layout wide agar dashboard muat
)

# --- Inisialisasi Session State ---
# Ini adalah "database" sementara kita untuk dashboard.
if 'issues' not in st.session_state:
    st.session_state['issues'] = []

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
        color: #FAFAFA; /* [PERBAIKAN] Atur default text color jadi putih */
    }
    
    [data-testid="stSidebar"] h2 {
        color: #00AFFF; /* Biru terang untuk judul sidebar */
        border-bottom: 2px solid #262730;
        padding-bottom: 10px;
    }
    
    /* [PERBAIKAN] Target spesifik label input dan header form di sidebar */
    [data-testid="stSidebar"] .stForm h3, 
    [data-testid="stSidebar"] .stForm h2, 
    [data-testid="stSidebar"] .stForm label,
    [data-testid="stSidebar"] .stMarkdown {
        color: #FAFAFA !important; /* Pakai !important untuk memaksa */
    }
    
    /* Card styling untuk hasil */
    .result-card {
        background-color: #262730; /* Streamlit card dark */
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #31333F; /* Border gelap */
    }
    
    .result-card h3 {
        color: #FAFAFA; /* Teks header card putih */
        margin-top: 0;
        margin-bottom: 15px;
        border-bottom: 2px solid #31333F;
        padding-bottom: 10px;
    }
    
    .result-card p, .result-card ul li {
        color: #FAFAFA; /* Teks list putih */
    }

    /* Styling untuk st.metric */
    [data-testid="stMetric"] {
        background-color: #1E1E1E; /* Background metric lebih gelap */
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #31333F;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 16px;
        color: #AAAAAA; /* Label metric abu-abu muda */
    }
    
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 600;
        color: #00AFFF; /* Nilai metric biru terang */
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 18px;
        font-weight: 600;
    }

    /* Tombol sidebar */
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
    
    .stAlert {
        color: #333; /* Pastikan teks info box bisa dibaca jika light */
    }

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

# [BARU] Fungsi helper untuk Dashboard
def get_warning_status(last_date):
    """Menghitung sisa hari dan memberikan status warning."""
    if last_date is None:
        return "Tanggal Belum Diatur", "info"
        
    today = datetime.date.today()
    days_left = (last_date - today).days

    if days_left < 0:
        return f"Selesai / Terlewat ({days_left} hari)", "error"
    elif days_left == 0:
        return "HARI TERAKHIR!", "error"
    elif days_left <= 3:
        return f"Sisa {days_left} hari!", "warning"
    else:
        return f"Sisa {days_left} hari", "success"

def remove_issue(issue_id):
    """Fungsi untuk menghapus item dari session state berdasarkan ID unik."""
    st.session_state['issues'] = [
        issue for issue in st.session_state['issues'] if issue['id'] != issue_id
    ]

# ==============================================================================
#  sidebar INPUT DARI USER (IMPROVED LAYOUT)
# ==============================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Download_Indicator_Arrow.svg/2048px-Download_Indicator_Arrow.svg.png", width=50)
st.sidebar.title("Kalkulator Rights Issue")
st.sidebar.markdown("Masukkan data prospektus untuk menganalisis dan menyimpan ke dashboard.")

with st.sidebar.form("ri_form"):
    
    # --- GRUP 1: INFO EMITEN ---
    st.header("1. Info Emiten")
    stock_code = st.text_input("Kode Saham", placeholder="Contoh: BBYB")
    P_market = st.number_input(
        "Harga Pasar Saat Ini (Rp)",
        min_value=0, value=1000, step=50,
        help="Harga saham di pasar sebelum tanggal Cum-Date."
    )

    # --- GRUP 2: SKEMA RIGHTS ISSUE ---
    st.header("2. Skema Rights Issue")
    st.markdown("**Rasio (Lama : Baru)**")
    col_a, col_b = st.columns(2)
    N_old = col_a.number_input("Saham Lama", min_value=1, value=10, label_visibility="collapsed", help="Bagian 'Lama' dari rasio (Contoh: 10:3, masukkan 10)")
    N_new = col_b.number_input("Hak Tebus (Baru)", min_value=1, value=3, label_visibility="collapsed", help="Bagian 'Baru' dari rasio (Contoh: 10:3, masukkan 3)")
    
    P_exercise = st.number_input(
        "Harga Tebus / Exercise (Rp)",
        min_value=0, value=500, step=50,
        help="Harga untuk menebus 1 lembar saham baru."
    )
    
    st.markdown("**Tanggal Penting**")
    col_d1, col_d2 = st.columns(2)
    cum_date = col_d1.date_input("Cum Date", value=None)
    ex_date = col_d2.date_input("Ex Date", value=None)
    start_trading = col_d1.date_input("Start Trading", value=None)
    last_trading = col_d2.date_input("Last Trading (Warning!)", value=None)

    # --- GRUP 3: POSISI ANDA ---
    st.header("3. (Opsional) Posisi Anda")
    My_Shares = st.number_input(
        "Jumlah Saham Anda Saat Ini",
        min_value=0, value=1000, step=100,
        help="Jumlah saham yang Anda pegang (untuk simulasi dilusi)."
    )
    My_Avg_Price = st.number_input(
        "Harga Beli Rata-Rata Anda (Rp)",
        min_value=0.0, value=float(P_market), step=50.0, format="%.2f",
        help="Harga modal (average price) Anda saat ini. Default = Harga Pasar."
    )

    submit_button = st.form_submit_button("Hitung & Tambah ke Dashboard 🧮")

# ==============================================================================
# 📊 TAMPILAN UTAMA & HASIL
# ==============================================================================
st.title("💸 Analisis Kelayakan Rights Issue")

if not submit_button:
    st.info("Masukkan parameter *rights issue* di *sidebar* kiri dan klik 'Hitung & Tambah ke Dashboard'.")

# --- Logika setelah form disubmit ---
if submit_button:
    # Lakukan kalkulasi
    P_teori, Nilai_HMETD, Dilution_pct = calculate_theoretical_price(P_market, N_old, P_exercise, N_new)

    if not stock_code:
         st.error("Kode Saham wajib diisi!")
    else:
        st.markdown(f"Menganalisis skenario **{stock_code.upper()}** (**{N_old} : {N_new}**) dengan harga tebus **Rp {P_exercise:,.0f}** dan harga pasar **Rp {P_market:,.0f}**.")
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
                f"Anda 'diuntungkan' karena bisa membeli saham di harga tebus (Rp {P_exercise:,.0f}) yang jauh lebih murah daripada harga teorinya (Rp {P_teori:,.2f})."
            )
            
        st.info(
            f"**STRATEGI:** Anda **wajib menebus** semua hak Anda. Jika Anda tidak menebus, "
            f"saham Anda akan terdilusi dan nilainya akan turun sebesar **{Dilution_pct:,.2f}%** "
            f"secara cuma-cuma (rugi kertas) saat *ex-date*."
        )

        st.markdown("---")

        # --- Tampilan Simulasi (dengan PNL) ---
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
            
            # Handle division by zero
            New_Avg_Price = (Cost_Basis_After / Total_Shares_After) if Total_Shares_After > 0 else 0
            
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

        # --- Logika untuk menambah ke dashboard ---
        # Cek duplikat berdasarkan stock_code (opsional, tapi bagus)
        existing_codes = [issue['stock_code'] for issue in st.session_state['issues']]
        if stock_code.upper() not in existing_codes:
            new_issue = {
                "id": f"{stock_code}-{datetime.datetime.now().timestamp()}",
                "stock_code": stock_code.upper(),
                "harga_tebus": P_exercise,
                "harga_teori": P_teori, # Ambil dari kalkulasi di atas
                "cum_date": cum_date,
                "ex_date": ex_date,
                "start_trading": start_trading,
                "last_trading": last_trading,
            }
            # Tambahkan ke session state
            st.session_state['issues'].append(new_issue)
            st.success(f"Saham {stock_code.upper()} berhasil ditambahkan ke dashboard pantauan!")
        else:
            st.warning(f"Saham {stock_code.upper()} sudah ada di dashboard. Hapus dulu jika ingin update.")
        

# ==============================================================================
# TAMPILAN DASHBOARD PANTAUAN
# ==============================================================================
st.markdown("---")
st.header("📅 Dashboard Pantauan Saham", divider="rainbow")

if not st.session_state['issues']:
    st.info("Belum ada saham yang dipantau. Silakan tambahkan melalui form di sidebar.")
else:
    # Buat grid 3 kolom untuk kartu-kartu
    # [PERBAIKAN] Gunakan 3 kolom agar layout sesuai screenshot
    cols = st.columns(3) 
    
    # Urutkan berdasarkan 'last_trading' (yang paling mepet paling atas)
    sorted_issues = sorted(
        st.session_state['issues'], 
        key=lambda x: (x['last_trading'] or datetime.date.max, x['stock_code']) # Handle jika tanggal None
    )

    for idx, issue in enumerate(sorted_issues):
        warning_text, warning_type = get_warning_status(issue['last_trading'])
        
        # Taruh kartu di kolom yang sesuai (idx % 3 akan berputar 0, 1, 2)
        with cols[idx % 3]:
            
            with st.container(border=True):
                
                # Header Kartu
                col_h1, col_h2 = st.columns([4, 1])
                with col_h1:
                    st.subheader(f"Saham: {issue['stock_code']}")
                with col_h2:
                    # Tombol hapus dengan callback, kirim ID unik-nya
                    st.button("X", 
                              key=f"delete_{issue['id']}", 
                              on_click=remove_issue, 
                              args=(issue['id'],), # Kirim ID unik untuk dihapus
                              help="Hapus item ini")
                
                # Peringatan (paling penting!)
                if warning_type == "error":
                    st.error(f"**{warning_text}**")
                elif warning_type == "warning":
                    st.warning(f"**{warning_text}**")
                elif warning_type == "success":
                    st.success(f"**{warning_text}**")
                else:
                    st.info(f"**{warning_text}**") # Untuk status 'info'

                # Detail Harga (Layout 2 kolom seperti di screenshot)
                col_p1, col_p2 = st.columns(2)
                col_p1.metric("Harga Tebus", f"Rp {issue['harga_tebus']:,.2f}")
                col_p2.metric("Harga Teori", f"Rp {issue['harga_teori']:,.2f}")

                # Detail Tanggal
                st.markdown("---")
                st.markdown(f"""
                - **Cum Date**: `{issue['cum_date']}`
                - **Ex Date**: `{issue['ex_date']}`
                - **Start Trading**: `{issue['start_trading']}`
                - **Last Trading**: `{issue['last_trading']}`
                """)

st.markdown("---")
st.markdown("**Disclaimer:** Kalkulator ini hanya menghitung harga teori berdasarkan prospektus. Harga pasar riil di *ex-date* dapat berbeda karena sentimen pasar.")
