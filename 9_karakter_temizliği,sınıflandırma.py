import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Ürün Eşleştirme", layout="wide")
st.title("🔍 Ürün Kodu + Adı ile Fatura - Sipariş Eşleştirme")

# Fonksiyon: Normalizasyon
def normalize(text):
    return str(text).strip().lower() if pd.notna(text) else ""

# Fonksiyon: Eşleştirme işlemi
def eslestir(fatura_df, siparis_df, skor_esigi=90):
    eslesmeler = []
    eslesmeyenler = []

    for _, fatura in fatura_df.iterrows():
        best_score = 0
        best_match = None

        for _, siparis in siparis_df.iterrows():
            skor_kod = fuzz.token_set_ratio(fatura["norm_kod"], siparis["norm_kod"])
            skor_ad = fuzz.token_set_ratio(fatura["norm_ad"], siparis["norm_ad"])
            toplam_skor = 0.7 * skor_kod + 0.3 * skor_ad

            if toplam_skor > best_score:
                best_score = toplam_skor
                best_match = siparis

        if best_score >= skor_esigi:
            eslesmeler.append({
                "fatura_kodu": fatura["urun_kodu"],
                "fatura_adi": fatura["urun_adi"],
                "siparis_kodu": best_match["urun_kodu"],
                "siparis_adi": best_match["urun_adi"],
                "benzerlik_orani": round(best_score, 2),
                "durum": "KOD + AD EŞLEŞTİ"
            })
        else:
            eslesmeyenler.append({
                "fatura_kodu": fatura["urun_kodu"],
                "fatura_adi": fatura["urun_adi"],
                "durum": "EŞLEŞMEDİ"
            })

    return pd.DataFrame(eslesmeler), pd.DataFrame(eslesmeyenler)

# Excel'e yazmak için yardımcı fonksiyon
def dataframe_to_excel_bytes(df1, df2):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df1.to_excel(writer, index=False, sheet_name="Eslesen")
        df2.to_excel(writer, index=False, sheet_name="Eslesmeyen")
    buffer.seek(0)
    return buffer

# Dosya yükleme alanları
col1, col2 = st.columns(2)

with col1:
    fatura_file = st.file_uploader("📄 Fatura dosyasını yükleyin (.xlsx)", type=["xlsx"])

with col2:
    siparis_file = st.file_uploader("📄 Sipariş dosyasını yükleyin (.xlsx)", type=["xlsx"])

# Benzerlik eşiği ayarı
skor_esigi = st.slider("🎯 Benzerlik Eşiği (%)", min_value=50, max_value=100, value=90)

# İşlem
if fatura_file and siparis_file:
    try:
        df_fatura = pd.read_excel(fatura_file)
        df_siparis = pd.read_excel(siparis_file)

        # Normalizasyon
        df_fatura["norm_kod"] = df_fatura["urun_kodu"].apply(normalize)
        df_fatura["norm_ad"] = df_fatura["urun_adi"].apply(normalize)
        df_siparis["norm_kod"] = df_siparis["urun_kodu"].apply(normalize)
        df_siparis["norm_ad"] = df_siparis["urun_adi"].apply(normalize)

        df_eslesen, df_eslesmeyen = eslestir(df_fatura, df_siparis, skor_esigi)

        st.success("✅ Eşleştirme tamamlandı!")

        st.subheader("🔍 Eşleşen Ürünler")
        st.dataframe(df_eslesen, use_container_width=True)

        st.subheader("❌ Eşleşmeyen Ürünler")
        st.dataframe(df_eslesmeyen, use_container_width=True)

        # Excel indirme
        excel_bytes = dataframe_to_excel_bytes(df_eslesen, df_eslesmeyen)
        tarih = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Excel çıktısını indir",
            data=excel_bytes,
            file_name=f"eslestirme_sonuclari_{tarih}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Hata oluştu: {e}")
else:
    st.info("👆 Eşleştirme işlemi için lütfen iki Excel dosyası yükleyin.")
