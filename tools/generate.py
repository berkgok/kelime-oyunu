# -*- coding: utf-8 -*-
"""
Kelime Oyunu — kelime havuzu üreticisi.

Kaynaklar:
  - TDK Güncel Türkçe Sözlük dump'ı (ogun/guncel-turkce-sozluk, MIT)
  - Türkçe sıklık listesi (hermitdave/FrequencyWords, tr_50k)

Üretir: ../kelimeler.json  ->  [{w, c, d}, ...]
  w: kelime (Türkçe büyük harf)   c: tanım (cevap maskelenmiş)   d: 'k'|'o'|'z'

Çalıştır:  python tools/generate.py
"""
import sys, os, io, json, tarfile, re, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT  = os.path.join(HERE, "..", "kelimeler.json")
os.makedirs(DATA, exist_ok=True)

TDK_URL  = "https://raw.githubusercontent.com/ogun/guncel-turkce-sozluk/master/sozluk/v12/v12.gts.json.tar.gz"
FREQ_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/tr/tr_full.txt"
FREQ_FILE = "tr_full.txt"

# --- zorluk eşikleri (sıklık sırasına göre; düşük sıra = daha yaygın) ---
EASY_MAX = 6000      # rank < 6000   -> kolay
MED_MAX  = 20000     # 6000..20000   -> orta ;  20000+ -> zor
MAX_RANK = 90000     # bundan daha nadir kelimeleri alma (kalite sınırı)
# her (uzunluk, zorluk) kovasında en fazla kaç kelime (en yaygınlar seçilir)
CAP_PER_BUCKET = 700
MIN_LEN, MAX_LEN = 4, 10
MIN_DEF_LEN = 12     # bir anlamın değerlendirmeye alınması için en az uzunluk
MIN_GOOD    = 16     # nihai tanım bundan kısaysa muğlak kabul edilip elenir

TR_LOWER = set("abcçdefgğhıijklmnoöprsştuüvyzâîû")

# TDK'nın kaba/hakaret işaretleri (anlamın ozelliklerListe.kisa_adi)
VULGAR_MARKS = {"kaba", "hkr."}
# işaretsiz ama uygunsuz kelimeler için yedek kara liste
BLOCKLIST = {"piç", "gavat", "kaltak", "yosma", "ibne", "kahpe", "orospu",
             "pezevenk", "taşak", "yarak", "sik", "am", "göt", "bok"}

# köken (lisan) — yalnızca yabancı diller; "Türkçe" ve eponim/parantezliler hariç
LANGS = {"Arapça", "Fransızca", "Farsça", "İngilizce", "İtalyanca", "Rumca", "Almanca",
         "Latince", "Yunanca", "Rusça", "İspanyolca", "Ermenice", "Bulgarca", "Moğolca",
         "Macarca", "Japonca", "Sırpça", "İbranice", "Soğdca", "Sanskrit", "Çince",
         "Portekizce", "Norveççe", "Fince", "Slavca", "Korece", "Lehçe", "Hintçe"}

def fetch(url, path):
    if os.path.exists(path):
        return open(path, "rb").read()
    req = urllib.request.Request(url, headers={"User-Agent": "curl"})
    data = urllib.request.urlopen(req, timeout=180).read()
    open(path, "wb").write(data)
    return data

def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()

def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()

def deaccent(s):
    return s.replace("â", "a").replace("î", "i").replace("û", "u")

# ---------------------------------------------------------------- frekans
freq_raw = fetch(FREQ_URL, os.path.join(DATA, FREQ_FILE)).decode("utf-8")
freq = {}
for i, line in enumerate(freq_raw.strip().split("\n")):
    w = line.split(" ")[0].strip().lower()
    if w and w not in freq:
        freq[deaccent(w)] = i      # rank = satır indeksi

# ---------------------------------------------------------------- TDK dump
tgz = fetch(TDK_URL, os.path.join(DATA, "v12.gts.json.tar.gz"))
tf  = tarfile.open(fileobj=io.BytesIO(tgz))
f   = tf.extractfile("gts.json")

def is_ref(a):
    """yönlendirme/çapraz başvuru tanımı mı (bk., →, ► ...)"""
    a = a.strip()
    if not a:
        return True
    if a[0] in "→►◄<≈/":
        return True
    return a.lower().startswith(("bk.", "bakınız", "krş.", "bk ", "→"))

_VULGAR_TEXT = re.compile(r"\b(" + "|".join(re.escape(b) for b in BLOCKLIST if len(b) > 2) + r")\b", re.IGNORECASE)
SYMBOL = re.compile(r"[+=%×÷−]")                     # işaret tanımı (ör. ARTI -> "+")
TOKEN  = re.compile(r"[a-zçğıöşü]+")                 # tanımdaki kelimeler (deaccent sonrası)

def clean_def(anlam):
    """asıl tanım: fazla boşlukları sadeleştir, ilk ';' öncesini al (sonrası eş anlamlı listesi)."""
    t = re.sub(r"\s+", " ", anlam).strip()
    return t.split(";")[0].strip(" ,;:")

def reveals(word, c):
    """tanım, cevabı ya da aynı kökten türemiş bir kelimeyi içeriyor mu?
       (ör. ÇARESİZCE <- 'çaresiz', KAZI <- 'kazma', ARKADAŞLIK <- 'arkadaş')"""
    w = deaccent(tr_lower(word))
    L = len(w)
    thr = 3 if L <= 4 else (4 if L <= 6 else 5)      # ortak ön ek eşiği (uzunluğa göre)
    for t in TOKEN.findall(deaccent(tr_lower(c))):
        if len(t) < 3:
            continue
        n = 0
        for a, b in zip(w, t):
            if a == b:
                n += 1
            else:
                break
        if n >= thr:
            return True
    return False

def good_meaning(anlam, word):
    """bir anlamı temizleyip oyuna uygunsa döndürür, değilse None"""
    if not anlam or is_ref(anlam):
        return None
    c = clean_def(anlam)
    if len(c) < MIN_DEF_LEN or c[0].isdigit():
        return None
    if SYMBOL.search(c):                             # işaret tanımı (ör. ARTI -> "+ işareti")
        return None
    if _VULGAR_TEXT.search(c):                       # tanım metni kaba kelime içeriyor
        return None
    if reveals(word, c):                            # cevap veya aynı kökten kelime tanımda geçiyor
        return None
    return c

POS_MAP = {"a.": "isim", "sf.": "sıfat", "zf.": "zarf", "e.": "edat",
           "ünl.": "ünlem", "bağ.": "bağlaç", "zm.": "zamir"}

def pos_of(a):
    for o in (a.get("ozelliklerListe") or []):
        k = o.get("kisa_adi")
        if k in POS_MAP:
            return POS_MAP[k]
    return None

def is_mecaz(a):
    return any(o.get("kisa_adi") == "mec." for o in (a.get("ozelliklerListe") or []))

def choose_def(anlamlar, word):
    """Geçerli anlamlar arasından seç. Mümkünse mecaz OLMAYAN anlamı tercih et
       (mecaz anlamlar oyuncuyu yanıltabiliyor). Birincil anlam kaba ise kelimeyi ele.
       Döndürür: (anlam_objesi, temiz_tanım) ya da (None, None)."""
    valid = []   # (a, c, mecaz)
    for i, a in enumerate(anlamlar):
        marks = {o.get("kisa_adi") for o in (a.get("ozelliklerListe") or [])}
        if marks & VULGAR_MARKS:
            if i == 0:
                return (None, None)                  # birincil anlam kaba -> kelimeyi atla
            continue
        c = good_meaning((a.get("anlam") or "").strip(), word)
        if c:
            valid.append((a, c, "mec." in marks))
    if not valid:
        return (None, None)
    for a, c, mec in valid:                          # önce mecaz olmayan ilk geçerli anlam
        if not mec:
            return (a, c)
    return (valid[0][0], valid[0][1])                # hepsi mecazsa ilkini ver

# Aynı başmaddenin birden çok kaydı (homonim) olabilir; en zengin olanı tut.
seen = {}
for raw in f:
    try:
        e = json.loads(raw)
    except Exception:
        continue
    # kanonik başmadde (madde): doğru Türkçe yazım. madde_duz bazı kayıtlarda harf yutuyor.
    w = (e.get("madde") or e.get("madde_duz") or "").strip().lower()
    if not w:
        continue
    if not (MIN_LEN <= len(w) <= MAX_LEN):
        continue
    if any(ch not in TR_LOWER for ch in w):       # tek kelime, sadece harf
        continue
    if e.get("ozel_mi") not in (None, "0", 0):     # özel isim ele
        continue
    if e.get("cogul_mu") in ("1", 1):              # çoğul başmadde ele
        continue
    if w in BLOCKLIST:                             # uygunsuz (yedek kara liste)
        continue
    rank = freq.get(deaccent(w))
    if rank is None or rank >= MAX_RANK:           # sıklık listesinde yok ya da çok nadir -> ele
        continue
    anlamlar = e.get("anlamlarListe") or []
    if not anlamlar:
        continue
    a, c = choose_def(anlamlar, w)
    if not c or len(c) < MIN_GOOD:                 # muğlak/çok kısa tanımı ele
        continue
    d = "k" if rank < EASY_MAX else ("o" if rank < MED_MAX else "z")
    pos = pos_of(a) or pos_of(anlamlar[0]) or ("fiil" if w.endswith(("mak", "mek")) else "")
    mecaz = is_mecaz(a)
    lis = (e.get("lisan") or "").split(" ")[0]
    koken = lis if lis in LANGS else ""           # yabancı köken (Arapça, Fransızca...)
    score = (int(e.get("anlam_say") or 0), len(c))  # en çok anlamlı (asıl homonim), sonra en açıklayıcı
    prev = seen.get(w)
    if prev is None or score > prev["_score"]:
        seen[w] = {"w": tr_upper(w), "c": c, "d": d, "t": pos, "m": 1 if mecaz else 0,
                   "k": koken, "_r": rank, "_L": len(w), "_score": score}

# ---------------------------------------------------------------- kovalar + cap
buckets = {}   # (L,d) -> list
for o in seen.values():
    buckets.setdefault((o["_L"], o["d"]), []).append(o)

out = []
for (L, d), lst in buckets.items():
    lst.sort(key=lambda x: x["_r"])          # en yaygın önce
    for o in lst[:CAP_PER_BUCKET]:
        rec = {"w": o["w"], "c": o["c"], "d": o["d"]}
        if o.get("t"):
            rec["t"] = o["t"]            # tür: isim/sıfat/zarf/edat/fiil...
        if o.get("m"):
            rec["m"] = 1                 # mecazi anlam
        if o.get("k"):
            rec["k"] = o["k"]            # köken: Arapça/Fransızca...
        out.append(rec)

out.sort(key=lambda x: (len(x["w"]), x["d"], x["w"]))
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------- rapor
print("Toplam kelime:", len(out), "  (ham aday:", len(seen), ")")
print("Dosya boyutu:", round(os.path.getsize(OUT)/1024, 1), "KB")
print("\nUzunluk \\ zorluk     kolay  orta   zor   toplam")
for L in range(MIN_LEN, MAX_LEN+1):
    k = sum(1 for x in out if len(x["w"])==L and x["d"]=="k")
    o = sum(1 for x in out if len(x["w"])==L and x["d"]=="o")
    z = sum(1 for x in out if len(x["w"])==L and x["d"]=="z")
    print(f"  {L:>2} harf           {k:>5} {o:>5} {z:>5}   {k+o+z:>5}")
tot_k = sum(1 for x in out if x["d"]=="k")
tot_o = sum(1 for x in out if x["d"]=="o")
tot_z = sum(1 for x in out if x["d"]=="z")
print(f"\n  Zorluk dağılımı: kolay {tot_k}  orta {tot_o}  zor {tot_z}")
print("\nÖrnekler:")
for L in (4, 7, 10):
    for d in ("k","o","z"):
        ex = next((x for x in out if len(x["w"])==L and x["d"]==d), None)
        if ex: print(f"  [{L}h/{d}] {ex['w']}: {ex['c'][:70]}")
# en nadir (zor) birkaç kelime — kalite kontrolü
print("\nEn nadir 12 'zor' kelime (kalite kontrolü):")
zor = sorted([s for s in seen.values() if s['d']=='z'], key=lambda x:-x['_r'])[:12]
for o in zor:
    print(f"  rank~{o['_r']:>6}  {o['w']}: {o['c'][:55]}")
