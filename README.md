# 🎯 Kelime Oyunu

> Ali İhsan Varol'un sunduğu efsane TV yarışması **Kelime Oyunu** formatından ilham alınarak yapılmış, tarayıcıdan oynanabilen tek kişilik kelime bulmaca oyunu.

Tek bir `index.html` dosyası — kurulum yok, bağımlılık yok, sunucu yok. Aç ve oyna. 📱💻

**🎮 Canlı Demo:** [berkgok.github.io/kelime-oyunu](https://berkgok.github.io/kelime-oyunu/)
_(GitHub Pages'i etkinleştirdikten sonra bu adreste yayında olur — aşağıdaki [Online Yayınlama](#-online-yayınlama) bölümüne bakın.)_

---

## 🕹️ Nasıl Oynanır?

Sana bir kelimenin **tanımı** verilir, sen de o kelimeyi bulmaya çalışırsın.

- ⏱️ Toplam **4 dakika** süre ve **14 soru** vardır. Kelimeler **4 harften 10 harfe** doğru uzar.
- 🔤 Bir kelimenin harf sayısı kadar kutu görürsün. **Hiç harf almadan** bilirsen tam puan!
- 💡 **Harf Al** dersen rastgele bir harf açılır — ama her açılan harf, kelimenin değerini **100 puan** azaltır.
  - Örnek: 4 harflik bir kelime hiç harf almadan **400**, bir harf alınca **300**, iki harf alınca **200** puan kazandırır.
  - Tüm harfleri açarsan kelime **0 puanla** geçilir.
- 🎤 Cevaplamadan önce **CEVAPLA** butonuna bas — ardından **20 saniyen** vardır.
- ⚠️ Süre dolar ya da yanlış yazarsan, kelimenin **kalan değeri toplam puanından düşülür!**

Soruların yaklaşık **%60'ı kolay, %30'u orta, %10'u zordur** (zorluk, kelimenin günlük kullanım sıklığına göre belirlenir) — ama bu bilgi oyuncuya gösterilmez. 😉

---

## ✨ Özellikler

- 🎰 **Çarkıfelek harf animasyonu** — harf alındığında kutu, dönen harfler arasında yavaşlayarak doğru harfe oturur (ses efektiyle).
- 🎨 **TV stüdyo teması** — mor/mavi gradyan, ışıklı paneller, ışık huzmeleri.
- 🔊 **Web Audio ile ses efektleri** — harf, doğru/yanlış cevap ve geri sayım sesleri (kapatılabilir).
- 📱 **Tam mobil uyumlu** — telefon, tablet ve masaüstünde akışkan, taşmasız tasarım.
- 🏆 **Rekor kaydı** — en yüksek skorun tarayıcıya (`localStorage`) kaydedilir.
- 📚 **6800+ kelimelik havuz** — TDK Güncel Türkçe Sözlük dump'ı, Türkçe sıklık listesiyle harmanlanarak üretilir; havuz `kelimeler.json` dosyasından yüklenir (yüklenemezse gömülü yedek havuza düşer).
- ⌨️ **Klavye desteği** — `H` ile harf al, `Boşluk` ile cevapla, `Enter` ile gönder.

---

## 🚀 Çalıştırma

### Yerelde

`index.html` dosyasına çift tıklaman yeterli — doğrudan tarayıcıda açılır.

İstersen küçük bir yerel sunucuyla da çalıştırabilirsin:

```bash
# Python 3
python -m http.server 5500
# Sonra tarayıcıda: http://localhost:5500
```

---

## 🌐 Online Yayınlama

Statik tek dosya olduğu için yayınlamak çok kolay ve ücretsizdir.

### GitHub Pages (önerilen — kalıcı adres)

1. Bu repoda **Settings → Pages** sayfasına git.
2. **Source** olarak `Deploy from a branch` seç.
3. **Branch:** `master`, klasör: `/ (root)` → **Save**.
4. Birkaç dakika içinde oyun şu adreste yayında olur:
   `https://berkgok.github.io/kelime-oyunu/`

### Netlify Drop (en hızlı — hesap gerekmez)

[app.netlify.com/drop](https://app.netlify.com/drop) adresine `index.html` dosyasını sürükle-bırak; anında bir link alırsın.

---

## 🛠️ Teknik Detaylar

- **Saf HTML + CSS + JavaScript** — hiçbir kütüphane veya derleme adımı yok.
- Tüm oyun mantığı, stiller ve kelime havuzu tek bir `index.html` içinde.
- Türkçe karakterler için yerele duyarlı karşılaştırma (`toLocaleUpperCase('tr-TR')`).
- Zamanlayıcılar, animasyonlar ve ses tamamen tarayıcı API'leriyle (`setInterval`, Web Audio API).

---

## 📁 Proje Yapısı

```
kelime-oyunu/
├── index.html        # Oyunun tamamı (HTML + CSS + JS + gömülü yedek havuz)
├── kelimeler.json    # Asıl kelime havuzu (3000+ kelime, üretilmiş)
├── tools/
│   └── generate.py   # Havuzu üreten script (TDK dump + sıklık listesi)
└── README.md
```

## 🔄 Kelime Havuzunu Yenileme / Genişletme

`kelimeler.json`, [TDK Güncel Türkçe Sözlük dump'ı](https://github.com/ogun/guncel-turkce-sozluk) ve
[Türkçe sıklık listesi](https://github.com/hermitdave/FrequencyWords) işlenerek üretilir. Yeniden
oluşturmak veya eşikleri (zorluk dağılımı, havuz boyutu) değiştirmek için:

```bash
python tools/generate.py
```

Script; kaynakları indirir, tek kelime + 4–10 harf + özel ad olmayan maddeleri filtreler,
sıklık listesiyle eşleştirip **kolay/orta/zor** etiketler, tanımı temizleyip cevabı maskeler
ve `kelimeler.json` dosyasını yazar. Eşikler dosyanın başındaki sabitlerden ayarlanabilir
(`EASY_MAX`, `MED_MAX`, `CAP_PER_BUCKET`).

---

## 📝 Notlar

- Kelime tanımları **TDK Güncel Türkçe Sözlük**'ten uyarlanmıştır.
- Bu proje, TRT/Bloomberg HT'de yayınlanan **Kelime Oyunu** programının formatından ilham almıştır; resmî bir bağı yoktur, eğitim ve eğlence amaçlıdır.

---

## 📄 Lisans

[MIT](LICENSE) — dilediğin gibi kullan, değiştir ve paylaş.
