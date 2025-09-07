# Deteksi Teks V2

Aplikasi web untuk mendeteksi dan mengekstrak tabel dari gambar menggunakan Streamlit dan PaddleOCR.

## Fitur
- Deteksi tabel pada gambar (misal: hasil scan dokumen)
- Ekstraksi data tabel ke format DataFrame (Pandas)
- Transformasi data tabel (misal: tabel Bulan x Tanggal)
- Antarmuka pengguna berbasis web dengan Streamlit

## Cara Menjalankan
1. **Install dependensi**
   
   Pastikan Python 3.8+ sudah terpasang. Install semua dependensi dengan:
   ```bash
   pip install -r requirements.txt
   ```

2. **Jalankan aplikasi**
   
   ```bash
   streamlit run app.py
   ```

3. **Akses aplikasi**
   
   Buka browser ke alamat yang tertera di terminal (biasanya http://localhost:8501)

## Struktur File
- `app.py` : Kode utama aplikasi Streamlit
- `requirements.txt` : Daftar dependensi Python

## Catatan
- Aplikasi ini menggunakan PaddleOCR dan PaddlePaddle, pastikan sistem Anda kompatibel.
- Untuk hasil terbaik, gunakan gambar dengan kualitas baik dan tabel yang jelas.

## Lisensi
Proyek ini bebas digunakan untuk keperluan non-komersial.
