
# Deteksi Teks V2

Aplikasi web interaktif untuk mendeteksi, mengekstrak, dan mentransformasi tabel dari gambar menggunakan Streamlit dan PaddleOCR.

---

## Fitur Utama
- **Deteksi Tabel Otomatis**: Ekstraksi tabel dari gambar (PNG/JPG/JPEG) menggunakan PaddleOCR.
- **Transformasi Tabel**: Otomatis mengubah tabel ke format Bulan × Tanggal, cocok untuk data absensi, keuangan, dsb.
- **Pratinjau & Unduh**: Pratinjau hasil tabel dan unduh sebagai file Excel.
- **Antarmuka Web**: Mudah digunakan melalui browser dengan Streamlit.

---

## Cara Pakai
1. **Instalasi Dependensi**
   
   Pastikan Python 3.8+ sudah terpasang. Install semua dependensi:
   ```bash
   pip install -r requirements.txt
   ```

2. **Jalankan Aplikasi**
   
   ```bash
   streamlit run app.py
   ```

3. **Akses Aplikasi**
   
   Buka browser ke alamat yang tertera di terminal (biasanya http://localhost:8501)

4. **Upload Gambar**
   
   - Klik "Upload gambar tabel" dan pilih file gambar berisi tabel.
   - Tabel yang terdeteksi akan ditampilkan.
   - Hasil transformasi Bulan × Tanggal juga akan muncul.
   - Klik tombol unduh untuk menyimpan hasil ke Excel.

---

## Struktur Proyek
- `app.py` : Kode utama aplikasi Streamlit
- `requirements.txt` : Daftar dependensi Python
- `README.md` : Dokumentasi proyek

---

## Penjelasan Kode Utama
- **Ekstraksi Tabel**: Fungsi `ocr_tables` menggunakan PaddleOCR untuk mendeteksi dan mengekstrak tabel dari gambar.
- **Transformasi**: Fungsi `build_bulan_x_tanggal` mengubah tabel ke format Bulan × Tanggal, otomatis mengenali pola input.
- **UI Streamlit**: Pengguna dapat mengunggah gambar, melihat hasil, dan mengunduh tabel.

---

## Catatan Penting
- **Kompatibilitas**: PaddleOCR dan PaddlePaddle membutuhkan sistem yang kompatibel (CPU/OS). Jika ada error instalasi, cek dokumentasi PaddleOCR.
- **Kualitas Gambar**: Untuk hasil terbaik, gunakan gambar dengan resolusi dan kontras yang baik.
- **Format Tabel**: Dirancang untuk tabel bulanan (absensi, keuangan, dsb) dengan header bulan/tanggal.

---

## Lisensi
Proyek ini bebas digunakan untuk keperluan non-komersial dan edukasi.

---

## Kontributor
- [Nama Anda]

---

## Referensi
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
