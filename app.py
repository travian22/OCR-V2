import io, os, re, tempfile
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

# ---------- Konstanta ----------
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
    s = str(x).strip().lower()
    s = s.replace(" ", "").replace("-", "")
    return MONTH_MAP.get(s)

def to_float(v):
    if pd.isna(v): return np.nan
    s = str(v).strip().replace(",", ".")
    s = re.sub(r"[^0-9\.\-]", "", s)
    try: return float(s)
    except: return np.nan

# ---------- Import PP-Structure ----------
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
    return PPStructure(layout=True, ocr=True, show_log=False)

@st.cache_data(show_spinner=False)
def ocr_tables(img_bytes: bytes):
    engine = get_engine()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    tmp = tempfile.mkdtemp()
    p = os.path.join(tmp, "img.png")
    img.save(p, "PNG")
    res = engine(p)
    out = []
    for r in res:
        if r.get("type") == "table":
            html = (r.get("res", {}) or {}).get("html") or r.get("html")
            if not html: continue
            try:
                out.append(pd.read_html(html)[0])
            except Exception:
                pass
    return out

# ---------- DETEKSI & TRANSFORM ----------
def build_bulan_x_tanggal(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Kembalikan tabel dengan:
      kolom-0 = 'Bulan' (Jan..Des),
      kolom 1..31 = tanggal
    Menangani 2 pola input:
      A) kolom-0 = Bulan, kolom lain = Tanggal (1..31)
      B) kolom-0 = Tanggal, kolom lain = Bulan (1..12 / Jan..Des)
    """
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
        import numpy as np, re, pandas as pd
        if pd.isna(v): return np.nan
        s = str(v).strip().replace(",", ".")
        s = re.sub(r"[^0-9\.\-]", "", s)
        try: return float(s)
        except: return np.nan

    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=["Bulan"] + list(range(1,32)))

    df = df_raw.copy()

    # buang baris rata-rata
    first = df.columns[0]
    df = df[~df[first].astype(str).str.contains("rata", case=False, na=False)]

    # deteksi pola: apakah kolom-0 mostly tanggal (1..31)?
    numerik_ratio = pd.to_numeric(df[first], errors="coerce").between(1,31).mean()

    if numerik_ratio >= 0.7:
        # ===== POLA B: kolom-0 = Tanggal, kolom lain = Bulan =====
        df = df.rename(columns={first: "Tanggal"}).reset_index(drop=True)

        # normalisasi header bulan
        new_cols = []
        for c in df.columns:
            if c == "Tanggal":
                new_cols.append("Tanggal")
            else:
                new_cols.append(std_month(c))  # angka 1..12 / nama → Jan..Des (None jika tak cocok)
        df.columns = new_cols
        # keep hanya kolom bulan valid + Tanggal
        keep = ["Tanggal"] + [m for m in df.columns if m in MONTHS_STD]
        df = df[keep]

        # tipe Tanggal → int agar pivot kolomnya integer, bukan string
        df["Tanggal"] = pd.to_numeric(df["Tanggal"], errors="coerce")
        df = df.dropna(subset=["Tanggal"])
        df["Tanggal"] = df["Tanggal"].astype(int)

        # nilai → float
        for c in df.columns:
            if c != "Tanggal":
                df[c] = df[c].map(to_float)

        # melt → pivot: Bulan jadi index, Tanggal jadi kolom
        long = df.melt(id_vars=["Tanggal"], var_name="Bulan", value_name="val")
        long = long[long["Bulan"].isin(MONTHS_STD)]
        tbl = long.pivot_table(index="Bulan", columns="Tanggal", values="val", aggfunc="first")

        # pastikan kolom bertipe int
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

        # header tanggal → int, drop yang gagal
        newc = []
        for c in df.columns:
            if c == "Bulan": newc.append("Bulan")
            else:
                try: newc.append(int(pd.to_numeric(c, errors="raise")))
                except Exception: newc.append(None)
        df.columns = newc
        df = df[[c for c in df.columns if (c == "Bulan") or isinstance(c, int)]]

        for c in df.columns:
            if c != "Bulan":
                df[c] = df[c].map(to_float)

        tbl = df.set_index("Bulan")

    # reindex baris & kolom target
    tbl = tbl.reindex(index=MONTHS_STD)
    tbl = tbl.reindex(columns=list(range(1,32)))

    # jadikan kolom-0 = "Bulan"
    tbl = tbl.reset_index().rename(columns={"index": "Bulan"})
    return tbl

# ---------- UI ----------
st.set_page_config(page_title="Bulan × Tanggal (Auto-fix)", layout="wide")
st.title("Tabel Kedua — Bulan × Tanggal (auto deteksi pola)")

up = st.file_uploader("Upload gambar tabel (.png/.jpg/.jpeg)", type=["png","jpg","jpeg"])
if up:
    b = up.read()
    st.image(Image.open(io.BytesIO(b)), caption="Gambar Masukan")

    with st.spinner("Membaca tabel..."):
        tables = ocr_tables(b)

    if not tables:
        st.error("Tidak ada tabel terdeteksi.")
    else:
        for i, t in enumerate(tables, 1):
            st.subheader(f"🟦 Tabel Utama #{i}")
            st.dataframe(t)

            st.subheader(f"🟩 Tabel Kedua #{i} — Bulan × Tanggal")
            out = build_bulan_x_tanggal(t)   # <-- pakai fungsi di atas
            st.dataframe(out)

            buf = io.BytesIO()
            with pd.ExcelWriter(buf) as w:
                out.to_excel(w, index=False, sheet_name="Bulan×Tanggal")
            st.download_button(
                f"💾 Unduh Tabel #{i}",
                data=buf.getvalue(),
                file_name=f"bulan_x_tanggal_{i}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
