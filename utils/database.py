# utils/database.py
import yfinance as yf

def muat_data_rupiah(periode):
    """Mengambil data historis kurs USD/IDR dari Yahoo Finance"""
    ticker = yf.Ticker("IDR=X")
    df = ticker.history(period=periode)
    if not df.empty:
        df.reset_index(inplace=True)
        df['Date'] = df['Date'].dt.tz_localize(None) # Hilangkan info timezone
    return df