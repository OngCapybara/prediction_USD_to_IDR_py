# app.py
import streamlit as app_st
import pandas as pd
import plotly.graph_objects as go

# PANGGIL MODUL YANG KITA BUAT DI FOLDER UTILS
from utils.database import muat_data_rupiah
from utils.prediksi import hitung_prediksi_multi_skenario

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA
# ==========================================
app_st.set_page_config(
    page_title="Analisis & Proyeksi Kurs Rupiah", 
    layout="wide",
    page_icon="📈"
)

app_st.title("📈 Analisis & Proyeksi Kurs Rupiah (USD/IDR)")
app_st.write(
    "Aplikasi Web Full-Stack berbasis Data Science untuk memantau pergerakan nilai tukar Rupiah "
    "lengkap dengan simulasi 3 skenario proyeksi ke depan."
)

# ==========================================
# 2. SIDEBAR - PENGATURAN PARAMETER
# ==========================================
app_st.sidebar.header("⚙️ Pengaturan Analisis")
app_st.sidebar.write("Pilih Rentang Waktu Historis:")

# Menggunakan pills sebagai pengganti dropdown
rentang = app_st.sidebar.pills(
    label="Rentang Waktu", # Judul internal (bisa dikosongkan dengan label_visibility="collapsed")
    options=["7 Hari Terakhir", "1 Bulan Terakhir", "3 Bulan Terakhir", "1 Tahun Terakhir"],
    default="1 Bulan Terakhir", # Pilihan awal saat web dibuka
    label_visibility="collapsed" # Menyembunyikan label duplikat agar rapi
)

# Pemetaan pilihan teks ke format kode yfinance (period)
pemetaan_waktu = {
    "7 Hari Terakhir": "7d", 
    "1 Bulan Terakhir": "1mo", 
    "3 Bulan Terakhir": "3mo", 
    "1 Tahun Terakhir": "1y"
}
periode_terpilih = pemetaan_waktu[rentang]

# ==========================================
# 3. PROSES AMBIL DATA & HITUNG PREDIKSI
# ==========================================
# Menggunakan fitur cache Streamlit agar aplikasi cepat dan tidak terkena blokir Yahoo Finance
@app_st.cache_data(ttl=3600)
def dapatkan_data_bersih(periode):
    return muat_data_rupiah(periode)

with app_st.spinner("Mengambil data kurs terbaru dari server..."):
    data = dapatkan_data_bersih(periode_terpilih)

if data.empty:
    app_st.error("Gagal mengambil data dari server. Silakan periksa koneksi internet Anda atau coba lagi nanti.")
else:
    # Jalankan perhitungan 3 skenario prediksi dari folder utils
    df_prediksi = hitung_prediksi_multi_skenario(data)
    
    # Ambil variabel penting untuk ringkasan metrik
    harga_sekarang = data['Close'].iloc[-1]
    harga_sebelumnya = data['Close'].iloc[-2]
    perubahan = harga_sekarang - harga_sebelumnya
    persen_perubahan = (perubahan / harga_sebelumnya) * 100

    # ==========================================
    # 4. TAMPILAN INTERFACES - KARTU METRIK
    # ==========================================
    app_st.write("---")
    col1, col2, col3 = app_st.columns(3)
    
    with col1:
        app_st.metric(
            label="Kurs Hari Ini (USD ke IDR)", 
            value=f"Rp {harga_sekarang:,.2f}", 
            delta=f"{perubahan:,.2f} ({persen_perubahan:.2f}%)", 
            delta_color="inverse" # Merah jika naik (Rupiah melemah), Hijau jika turun (Rupiah menguat)
        )
    with col2:
        target_menguat = df_prediksi['Skenario_Menguat'].iloc[2]
        app_st.metric(
            label="Target Menguat Terbaik (Hari ke-3)", 
            value=f"Rp {target_menguat:,.2f}", 
            delta="Skenario Bullish", 
            delta_color="normal"
        )
    with col3:
        risiko_melemah = df_prediksi['Skenario_Melemah'].iloc[2]
        app_st.metric(
            label="Risiko Melemah Terburuk (Hari ke-3)", 
            value=f"Rp {risiko_melemah:,.2f}", 
            delta="Skenario Bearish", 
            delta_color="inverse"
        )

    # ==========================================
    # 5. TAMPILAN INTERFACES - GRAFIK MULTI SKENARIO
    # ==========================================
    app_st.write("---")
    app_st.subheader(f"📊 Visualisasi Tren Historis dan Proyeksi Corong 3 Hari ({rentang})")
    
    fig = go.Figure()
    
    # 1. Plot Garis Historis (Data Riwayat Nyata)
    fig.add_trace(go.Scatter(
        x=data['Date'], 
        y=data['Close'], 
        mode='lines+markers', 
        name='Data Historis (Riwayat)', 
        line=dict(color='#2c3e50', width=2)
    ))
    
    # Membuat sambungan tanggal agar grafik proyeksi tidak terputus dari titik hari ini
    tanggal_sambung = [data['Date'].iloc[-1]] + list(df_prediksi['Date'])
    
    # 2. Plot Proyeksi Skenario Melemah (Batas Atas / Bearish)
    nilai_melemah = [harga_sekarang] + list(df_prediksi['Skenario_Melemah'])
    fig.add_trace(go.Scatter(
        x=tanggal_sambung, 
        y=nilai_melemah, 
        mode='lines+markers', 
        name='⚠️ Skenario Melemah (Rupiah Depresiasi)', 
        line=dict(color='#e74c3c', width=2, dash='dash')
    ))
    
    # 3. Plot Proyeksi Tren Utama (Base Case)
    nilai_utama = [harga_sekarang] + list(df_prediksi['Tren_Utama'])
    fig.add_trace(go.Scatter(
        x=tanggal_sambung, 
        y=nilai_utama, 
        mode='lines+markers', 
        name='🔄 Tren Saat Ini (Garis Regresi)', 
        line=dict(color='#f39c12', width=2, dash='dash')
    ))
    
    # 4. Plot Proyeksi Skenario Menguat (Batas Bawah / Bullish)
    nilai_menguat = [harga_sekarang] + list(df_prediksi['Skenario_Menguat'])
    fig.add_trace(go.Scatter(
        x=tanggal_sambung, 
        y=nilai_menguat, 
        mode='lines+markers', 
        name='✅ Skenario Menguat (Rupiah Apresiasi)', 
        line=dict(color='#2ecc71', width=2, dash='dash')
    ))
    
    # Konfigurasi Layout Grafik agar Responsif dan Interaktif
    fig.update_layout(
        xaxis_title="Tanggal", 
        yaxis_title="Nilai Tukar Rupiah per 1 USD", 
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    app_st.plotly_chart(fig, use_container_width=True)
    
    # ==========================================
    # 6. TAMPILAN INTERFACES - TABEL DETAIL ANGKA
    # ==========================================
    app_st.write("---")
    col_info, col_tabel = app_st.columns([2, 3])
    
    with col_info:
        app_st.subheader("💡 Cara Membaca Skenario Proyeksi")
        app_st.markdown(
            """
            Proyeksi masa depan di atas dihitung secara sistematis menggunakan gabungan metode **Regresi Linier** dan tingkat **Volatilitas Historis** pasar:
            
            * **Skenario Melemah (Garis Merah):** Batas aman atas jika kondisi pasar tiba-tiba memburuk atau ada tekanan ekonomi luar negeri (Dollar menguat tajam).
            * **Tren Utama (Garis Kuning):** Ke mana arah harga melaju jika kondisi pasar berjalan normal dan stabil mengikuti pola beberapa hari terakhir.
            * **Skenario Menguat (Garis Hijau):** Batas optimis bawah jika intervensi Bank Indonesia berhasil atau terjadi aliran dana masuk ke pasar dalam negeri.
            
            _**Disclaimer:** Model matematika ini ditujukan hanya sebagai alat bantu analisis teknis jangka pendek dan tidak menjamin kepastian pergerakan pasar 100%._
            """
        )
        
    with col_tabel:
        app_st.subheader("📋 Angka Detail Hasil Simulasi Proyeksi")
        
        # Membuat duplikasi dataframe untuk merapikan tampilan tabel di website
        df_tabel = df_prediksi.copy()
        df_tabel['Date'] = df_tabel['Date'].dt.strftime('%A, %Y-%m-%d')
        df_tabel['Skenario Menguat (Bullish)'] = df_tabel['Skenario_Menguat'].map(lambda x: f"Rp {x:,.2f}")
        df_tabel['Tren Utama (Base Case)'] = df_tabel['Tren_Utama'].map(lambda x: f"Rp {x:,.2f}")
        df_tabel['Skenario Melemah (Bearish)'] = df_tabel['Skenario_Melemah'].map(lambda x: f"Rp {x:,.2f}")
        
        kolom_pilihan = ['Date', 'Skenario Menguat (Bullish)', 'Tren Utama (Base Case)', 'Skenario Melemah (Bearish)']
        app_st.dataframe(df_tabel[kolom_pilihan], hide_index=True, use_container_width=True)