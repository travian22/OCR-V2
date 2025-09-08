# app.py — OCR Tabel (PP-Structure) ➜ Tabel Kedua: Bulan × Tanggal
# Fokus stabilitas di Windows: tanpa MKL-DNN, limit thread, downscale gambar.

# ==== ENV STABILISASI (taruh paling atas, sebelum import Paddle) ====
import os
os.environ["FLAGS_use_mkldnn"] = "0"     # matikan oneDNN/MKL-DNN (biang crash)
os.environ["OMP_NUM_THREADS"]   = "1"     # batasi OpenMP (1–4 aman)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import io, re, tempfile
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

# ================== Konstanta & util ==================
MONTHS_STD = ["Jan","Peb","Mar","Apr","Mei","Jun","Jul","Ags","Sep","Okt","Nop","Des"]
MONTH_MAP = {
    "1":"Jan","jan":"Jan","jan.":"Jan",
    "2":"Peb","peb":"Peb","feb":"Peb","februari":"Peb",
    "3":"Mar","mar":"Mar",
    "4":"Apr","apr":"Apr",
    "5":"Mei","mei":"Mei","may":"Mei",
    "6":"Jun","jun":"Jun","juni":"Jun",
    "7":"Jul","jul":"Jul","juli":"Jul",
    "8":"Ags","ags":"Ags","agt":"Ags","aug":"Ags",
    "9":"Sep","sep":"Sep","sept":"Sep",
    "10":"Okt","okt":"Okt","oct":"Okt",
    "11":"Nop","nop":"Nop","nov":"Nop","november":"Nop",
    "12":"Des","des":"Des","dec":"Des",
}
def std_month(x):
    if x is None: return None
    s = str(x).strip().lower().replace(" ", "").replace("-", "")
    return MONTH_MAP.get(s)

def to_float(v):
    if pd.isna(v): return np.nan
    s = str(v).strip().replace(",", ".")
    s = re.sub(r"[^0-9\.\-]", "", s)
    try: return float(s)
    except: return np.nan

def pil_max_side(img: Image.Image, max_side=1600) -> Image.Image:
    w, h = img.size
    m = max(w, h)
    if m <= max_side:
        return img
    s = max_side / float(m)
    return img.resize((int(w*s), int(h*s)), Image.LANCZOS)

# ================== PP-Structure (safe mode) ==================
def _get_PPStructure():
    try:
        from paddleocr.ppstructure import PPStructure
        return PPStructure
    except Exception:
        from paddleocr import PPStructure
        return PPStructure

@st.cache_resource
def get_engine():
    PPStructure = _get_PPStructure()
    # SAFE: CPU only, no MKL-DNN, limit threads, kecilkan sisi deteksi
    return PPStructure(
        layout=True, ocr=True, show_log=False,
        use_gpu=False, use_mkldnn=False,
        cpu_threads=2,             # boleh 1–4
        det_limit_side_len=1280,   # jangan terlalu besar
        rec_batch_num=4,
    )

@st.cache_data(show_spinner=False)
def ocr_tables(img_bytes: bytes):
    """Jalankan PP-Structure dan kembalikan list DataFrame tabel mentah."""
    eng = get_engine()

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = pil_max_side(img, 1600)

    tmp = tempfile.mkdtemp()
    p = os.path.join(tmp, "in.png")
    img.save(p, "PNG")

    # Fallback otomatis jika crash
    try:
        res = eng(p)
    except RuntimeError:
        st.cache_resource.clear()
        PPStructure = _get_PPStructure()
        eng2 = PPStructure(
            layout=True, ocr=True, show_log=False,
            use_gpu=False, use_mkldnn=False,
            cpu_threads=1, det_limit_side_len=1024, rec_batch_num=2,
        )
        res = eng2(p)

    tables = []
    for r in res:
        if r.get("type") == "table":
            html = (r.get("res", {}) or {}).get("html") or r.get("html")
            if not html:
                continue
            try:
                tables.append(pd.read_html(html)[0])
            except Exception:
                pass
    return tables

# ================== Transform → Bulan × Tanggal ==================
def build_bulan_x_tanggal(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Hasilkan tabel dengan:
      kolom-0 = 'Bulan' (Jan..Des),
      kolom 1..31 = tanggal.
    Menangani 2 pola input:
      A) kolom-0 = Bulan, kolom lain = Tanggal (1..31)
      B) kolom-0 = Tanggal (1..31), kolom lain = Bulan (1..12/Jan..Des)
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=["Bulan"] + list(range(1,32)))

    df = df_raw.copy()

    # drop baris "Rata / Rata-rata"
    first = df.columns[0]
    df = df[~df[first].astype(str).str.contains("rata", case=False, na=False)]

    # deteksi pola via kolom-0
    numerik_ratio = pd.to_numeric(df[first], errors="coerce").between(1,31).mean()

    if numerik_ratio >= 0.7:
        # ===== POLA B: kolom-0 = Tanggal, kolom lain = Bulan =====
        df = df.rename(columns={first: "Tanggal"}).reset_index(drop=True)

        # normalisasi header bulan
        new_cols = []
        for c in df.columns:
            if c == "Tanggal": new_cols.append("Tanggal")
            else: new_cols.append(std_month(c))
        df.columns = new_cols
        keep = ["Tanggal"] + [c for c in df.columns if c in MONTHS_STD]
        df = df[keep]

        # Tanggal -> int (hindari string '1'..'31')
        df["Tanggal"] = pd.to_numeric(df["Tanggal"], errors="coerce")
        df = df.dropna(subset=["Tanggal"])
        df["Tanggal"] = df["Tanggal"].astype(int)

        # nilai -> float
        for c in df.columns:
            if c != "Tanggal":
                df[c] = df[c].map(to_float)

        # melt -> pivot (Bulan jadi baris, Tanggal jadi kolom)
        long = df.melt(id_vars=["Tanggal"], var_name="Bulan", value_name="val")
        long = long[long["Bulan"].isin(MONTHS_STD)]
        tbl = long.pivot_table(index="Bulan", columns="Tanggal", values="val", aggfunc="first")

        # pastikan kolom pivot bertipe int
        tbl.columns = pd.to_numeric(tbl.columns, errors="coerce")
        tbl = tbl.loc[:, ~tbl.columns.isna()]
        tbl.columns = tbl.columns.astype(int)

    else:
        # ===== POLA A: kolom-0 = Bulan, kolom lain = Tanggal =====
        months = [std_month(x) for x in df[first]]
        mask = [m in MONTHS_STD for m in months]
        df = df[mask].copy()
        df.insert(0, "Bulan", [m for m in months if m in MONTHS_STD])
        df = df.drop(columns=[first])

        # header tanggal -> int; drop kolom yang gagal di-cast
        newc = []
        for c in df.columns:
            if c == "Bulan":
                newc.append("Bulan")
            else:
                try: newc.append(int(pd.to_numeric(c, errors="raise")))
                except Exception: newc.append(None)
        df.columns = newc
        df = df[[c for c in df.columns if (c == "Bulan") or isinstance(c, int)]]

        # nilai -> float
        for c in df.columns:
            if c != "Bulan":
                df[c] = df[c].map(to_float)

        tbl = df.set_index("Bulan")

    # reindex baris & kolom target
    tbl = tbl.reindex(index=MONTHS_STD)
    tbl = tbl.reindex(columns=list(range(1,32)))

    # kolom-0 jadi "Bulan"
    tbl = tbl.reset_index().rename(columns={"index": "Bulan"})
    return tbl

# ================== UI ==================
st.set_page_config(page_title="OCR → Bulan × Tanggal (Safe)", layout="wide")
st.title("OCR Tabel (PP-Structure) → Tabel Kedua: Bulan × Tanggal")

up = st.file_uploader("Upload gambar tabel (.png/.jpg/.jpeg)", type=["png","jpg","jpeg"])
if up:
    img_bytes = up.read()
    st.image(Image.open(io.BytesIO(img_bytes)), caption="Gambar Masukan")

    with st.spinner("Mendeteksi & mengekstrak tabel..."):
        raw_tables = ocr_tables(img_bytes)

    if not raw_tables:
        st.error("Tidak ada tabel terdeteksi.")
    else:
        for i, tdf in enumerate(raw_tables, 1):
            st.subheader(f"🟦 Tabel Utama #{i}")
            st.dataframe(tdf)

            st.subheader(f"🟩 Tabel Kedua #{i} — Bulan × Tanggal")
            out = build_bulan_x_tanggal(tdf)
            st.dataframe(out)

            # Download Excel
            buf = io.BytesIO()
            with pd.ExcelWriter(buf) as w:
                out.to_excel(w, index=False, sheet_name="Bulan×Tanggal")
            st.download_button(
                f"💾 Unduh Tabel #{i}",
                data=buf.getvalue(),
                file_name=f"bulan_x_tanggal_{i}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
