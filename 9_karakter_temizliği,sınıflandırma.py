!pip install lxml rapidfuzz openpyxl
from google.colab import files
from lxml import etree
import re
from rapidfuzz import fuzz as rapidfuzz_fuzz
import pandas as pd
from IPython.display import display

# Normalizasyon fonksiyonu
def normalize(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

# Ürün kodu ve adı çıkaran fonksiyon
def urun_kodlarini_ve_adlarini_bul(dosya_yolu, min_karakter=5, max_karakter=15):
    tree = etree.parse(dosya_yolu)
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

# XML dosyalarını yükle
print("📤 Lütfen önce siparis.xml dosyasını yükleyin:")
uploaded1 = files.upload()
siparis_dosyasi = list(uploaded1.keys())[0]

print("\n📤 Şimdi fatura.xml dosyasını yükleyin:")
uploaded2 = files.upload()
fatura_dosyasi = list(uploaded2.keys())[0]

# Ürünleri al
siparis_listesi = urun_kodlarini_ve_adlarini_bul(siparis_dosyasi)
fatura_listesi = urun_kodlarini_ve_adlarini_bul(fatura_dosyasi)

# Normalize edilmiş sütunlar ekle
for kayit in siparis_listesi:
    kayit["norm_kod"] = normalize(kayit["urun_kodu"])
    kayit["norm_ad"] = normalize(kayit["urun_adi"])

for kayit in fatura_listesi:
    kayit["norm_kod"] = normalize(kayit["urun_kodu"])
    kayit["norm_ad"] = normalize(kayit["urun_adi"])
    # Eşleştirme işlemi (kod + ürün adı üzerinden)
eslesmeler = []
eslesmeyenler = []

for fatura in fatura_listesi:
    best_score = 0
    best_match = None

    for siparis in siparis_listesi:
        skor_kod = rapidfuzz_fuzz.token_set_ratio(fatura["norm_kod"], siparis["norm_kod"])
        skor_ad = rapidfuzz_fuzz.token_set_ratio(fatura["norm_ad"], siparis["norm_ad"])

        # Ağırlıklı ortalama
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

# DataFrame'ler
df_eslesen = pd.DataFrame(eslesmeler)
df_eslesmeyen = pd.DataFrame(eslesmeyenler)

# Ekranda göster
print("✅ Eşleşen Ürünler:")
display(df_eslesen)

print("\n🚫 Eşleşmeyen Ürünler:")
display(df_eslesmeyen)

# Excel'e yaz
df_eslesen.to_excel("eslesen_kod_ve_ad.xlsx", index=False)
df_eslesmeyen.to_excel("eslesmeyen_kod_ve_ad.xlsx", index=False)

print("📁 Excel çıktıları hazır.")

# İndirilebilir hale getir
files.download("eslesen_kod_ve_ad.xlsx")
files.download("eslesmeyen_kod_ve_ad.xlsx")
