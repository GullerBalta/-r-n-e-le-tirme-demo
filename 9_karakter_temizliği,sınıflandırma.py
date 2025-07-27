import streamlit as st
from lxml import etree
import re
from rapidfuzz import fuzz as rapidfuzz_fuzz
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Ürün Kod Eşleştirme", layout="wide")
st.title("🔍 XML Ürün Kodları Eşleştirme Aracı")

# Normalizasyon fonksiyonu
def normalize(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

# XML'den ürün kodlarını ve adlarını çıkaran fonksiyon
def urun_kodlarini_ve_adlarini_bul(xml_bytes, min_karakter=5, max_karakter=15):
    tree = etree.parse(xml_bytes)
    root = tree.getroot()
    kayitlar = []

    for eleman in root.iter():
        if eleman.text:
            metin = eleman.text.strip()
            kodlar = re.findall(r'\b[A-Za-z0-9\-\.]{%d,%d}\b' % (min_karakter, max_karakter), metin)

            for kod in kodlar:
                kayitlar.append({
                    "urun_kodu": kod,
                    "urun_adi": metin
                })

    return kayitlar[:500]

# XML dosyaları yükleme
siparis_dosyasi = st.file_uploader("📤 Sipariş XML dosyasını yükleyin", type=["xml"])
fatura_dosyasi = st.file_uploader("📤 Fatura XML dosyasını yükleyin", type=["xml"])

if siparis_dosyasi and fatura_dosyasi:
    siparis_listesi = urun_kodlarini_ve_adlarini_bul(siparis_dosyasi)
    fatura_listesi = urun_kodlarini_ve_adlarini_bul(fatura_dosyasi)

    # Normalize edilmiş sütunlar
    for kayit in siparis_listesi:
        kayit["norm_kod"] = normalize(kayit["urun_kodu"])
        kayit["norm_ad"] = normalize(kayit["urun_adi"])

    for kayit in fatura_listesi:
        kayit["norm_kod"] = normalize(kayit["urun_kodu"])
        kayit["norm_ad"] = normalize(kayit["urun_adi"])

    # Eşleştirme işlemi
    eslesmeler = []
    eslesmeyenler = []

    for fatura in fatura_listesi:
        best_score = 0
        best_match = None

        for siparis in siparis_listesi:
            skor_kod = rapidfuzz_fuzz.token_set_ratio(fatura["norm_kod"], siparis["norm_kod"])
            skor_ad = rapidfuzz_fuzz.token_set_ratio(fatura["norm_ad"], siparis["norm_ad"])

            toplam_skor = 0.7 * skor_kod + 0.3 * skor_ad

            if toplam_skor > best_score:
                best_score = toplam_skor
                best_match = siparis

        if best_score >= 90:
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

    # DataFrame oluştur
    df_eslesen = pd.DataFrame(eslesmeler)
    df_eslesmeyen = pd.DataFrame(eslesmeyenler)

    # Ekranda göster
    st.success("✅ Eşleşen Ürünler")
    st.dataframe(df_eslesen)

    st.error("🚫 Eşleşmeyen Ürünler")
    st.dataframe(df_eslesmeyen)

    # Excel çıktısı oluştur
    def to_excel_bytes(df1, df2):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df1.to_excel(writer, index=False, sheet_name="Eşleşenler")
            df2.to_excel(writer, index=False, sheet_name="Eşleşmeyenler")
        return output.getvalue()

    excel_data = to_excel_bytes(df_eslesen, df_eslesmeyen)
    st.download_button(
        label="📥 Excel İndir",
        data=excel_data,
        file_name="eslesme_raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("İki XML dosyasını da yükledikten sonra eşleştirme işlemi baş
