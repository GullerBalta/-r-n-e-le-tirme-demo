import pandas as pd
from rapidfuzz import fuzz
from datetime import datetime
import os
import platform

def eslestir_urunler(fatura_listesi, siparis_listesi, skor_esigi=90, dosya_adi_prefix="urun_eslestirme", indirme_modu="yerel"):
    eslesmeler = []
    eslesmeyenler = []

    for fatura in fatura_listesi:
        best_score = 0
        best_match = None

        for siparis in siparis_listesi:
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

    df_eslesen = pd.DataFrame(eslesmeler)
    df_eslesmeyen = pd.DataFrame(eslesmeyenler)

    tarih = datetime.now().strftime("%Y%m%d_%H%M%S")
    dosya1 = f"{dosya_adi_prefix}_eslesen_{tarih}.xlsx"
    dosya2 = f"{dosya_adi_prefix}_eslesmeyen_{tarih}.xlsx"

    df_eslesen.to_excel(dosya1, index=False)
    df_eslesmeyen.to_excel(dosya2, index=False)

    print("✅ Eşleşen Ürünler:")
    print(df_eslesen.to_string(index=False))

    print("\n🚫 Eşleşmeyen Ürünler:")
    print(df_eslesmeyen.to_string(index=False))

    print(f"\n📁 Excel çıktıları kaydedildi:\n - {dosya1}\n - {dosya2}")

    if indirme_modu == "yerel":
        try:
            if platform.system() == "Windows":
                os.startfile(dosya1)
                os.startfile(dosya2)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open {dosya1}")
                os.system(f"open {dosya2}")
            else:  # Linux
                os.system(f"xdg-open {dosya1}")
                os.system(f"xdg-open {dosya2}")
        except Exception as e:
            print(f"⚠️ Otomatik açma başarısız: {e}")

    return df_eslesen, df_eslesmeyen

# -----------------------------
# Test verisiyle çalıştırma:
# -----------------------------
if __name__ == "__main__":
    fatura_listesi = [
        {"urun_kodu": "ABC123", "urun_adi": "Kalem Kırmızı", "norm_kod": "abc123", "norm_ad": "kalem kirmizi"},
        {"urun_kodu": "DEF456", "urun_adi": "Silgi Küçük", "norm_kod": "def456", "norm_ad": "silgi kucuk"}
    ]

    siparis_listesi = [
        {"urun_kodu": "ABC124", "urun_adi": "Kalem Renkli", "norm_kod": "abc124", "norm_ad": "kalem renkli"},
        {"urun_kodu": "DEF456", "urun_adi": "Silgi Küçük", "norm_kod": "def456", "norm_ad": "silgi kucuk"}
    ]

    eslestir_urunler(fatura_listesi, siparis_listesi, skor_esigi=85)
