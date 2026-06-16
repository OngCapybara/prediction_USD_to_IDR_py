# utils/prediksi.py
import numpy as np
import pandas as pd
from datetime import timedelta

def hitung_prediksi_multi_skenario(data, basis_hari=5):
    """Menghitung prediksi tren utama, skenario menguat, dan skenario melemah"""
    data_tren = data.tail(basis_hari).copy()
    
    # 1. Hitung Tren Utama (Regresi Linear)
    x = np.arange(len(data_tren))
    y = data_tren['Close'].values
    m, c = np.polyfit(x, y, 1)
    
    # 2. Hitung Volatilitas (Standar Deviasi dari perubahan harian)
    # Ini dipakai untuk menentukan seberapa jauh jarak garis atas dan bawah
    perubahan_harian = data['Close'].pct_change().dropna()
    volatilitas_persen = perubahan_harian.std() 
    nilai_volatilitas_rupiah = data['Close'].iloc[-1] * volatilitas_persen
    
    # Generate tanggal 3 hari ke depan (Hanya Senin - Jumat)
    tanggal_terakhir = data['Date'].iloc[-1]
    tanggal_prediksi = []
    current_date = tanggal_terakhir
    
    while len(tanggal_prediksi) < 3:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5: 
            tanggal_prediksi.append(current_date)
            
    # Hitung nilai untuk ketiga skenario
    tren_utama = []
    skenario_melemah = [] # Harga USD naik = Rupiah melemah
    skenario_menguat = [] # Harga USD turun = Rupiah menguat
    
    hari_ke = basis_hari
    for i in range(1, 4): # Untuk 3 hari ke depan
        pred_dasar = (m * hari_ke) + c
        
        # Jarak skenario makin melebar setiap harinya (efek ketidakpastian waktu)
        faktor_waktu = np.sqrt(i) 
        rentang_guncangan = nilai_volatilitas_rupiah * faktor_waktu
        
        tren_utama.append(pred_dasar)
        skenario_melemah.append(pred_dasar + rentang_guncangan)
        skenario_menguat.append(pred_dasar - rentang_guncangan)
        hari_ke += 1
        
    df_prediksi = pd.DataFrame({
        'Date': tanggal_prediksi,
        'Tren_Utama': tren_utama,
        'Skenario_Melemah': skenario_melemah,
        'Skenario_Menguat': skenario_menguat
    })
    
    return df_prediksi