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
FREQ_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/tr/tr_50k.txt"

# --- zorluk eşikleri (sıklık sırasına göre; düşük sıra = daha yaygın) ---
EASY_MAX = 6000      # rank < 6000  -> kolay
MED_MAX  = 18000     # 6000..18000  -> orta ;  > 18000 -> zor
# her (uzunluk, zorluk) kovasında en fazla kaç kelime (en yaygınlar seçilir)
CAP_PER_BUCKET = 350
MIN_LEN, MAX_LEN = 4, 10
MIN_DEF_LEN = 12

TR_LOWER = set("abcçdefgğhıijklmnoöprsştuüvyzâîû")

def fetch(url, path):
    if os.path.exists(path):
        return open(path, "rb").read()
    req = urllib.request.Request(url, headers={"User-Agent": "curl"})
    data = urllib.request.urlopen(req, timeout=180).read()
    open(path, "wb").write(data)
    return data

def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()

def deaccent(s):
    return s.replace("â", "a").replace("î", "i").replace("û", "u")

# ---------------------------------------------------------------- frekans
freq_raw = fetch(FREQ_URL, os.path.join(DATA, "tr_50k.txt")).decode("utf-8")
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

def clean_def(anlam, word):
    t = re.sub(r"\s+", " ", anlam).strip()
    # asıl tanımı al: ilk ";" öncesi (sonrası genelde eş anlamlı listesi)
    t = t.split(";")[0].strip()
    # cevabı maskele — yalnızca tam kelime eşleşmesi (kelime sınırlı)
    t = re.sub(r"\b" + re.escape(word) + r"\b", "…", t, flags=re.IGNORECASE)
    # çok uzunsa kısalt (son boşluktan kes)
    if len(t) > 150:
        t = t[:150].rsplit(" ", 1)[0] + "…"
    return t.strip(" ,;:")

seen = {}
for raw in f:
    try:
        e = json.loads(raw)
    except Exception:
        continue
    w = (e.get("madde_duz") or e.get("madde") or "").strip().lower()
    if not w or w in seen:
        continue
    if not (MIN_LEN <= len(w) <= MAX_LEN):
        continue
    if any(ch not in TR_LOWER for ch in w):       # tek kelime, sadece harf
        continue
    if e.get("ozel_mi") not in (None, "0", 0):     # özel isim ele
        continue
    if e.get("cogul_mu") in ("1", 1):              # çoğul başmadde ele
        continue
    rank = freq.get(deaccent(w))
    if rank is None:                               # sıklık listesinde yoksa (nadir) ele
        continue
    anlamlar = e.get("anlamlarListe") or []
    if not anlamlar:
        continue
    anlam = (anlamlar[0].get("anlam") or "").strip()
    if len(anlam) < MIN_DEF_LEN or is_ref(anlam):
        continue
    c = clean_def(anlam, w)
    if len(c) < MIN_DEF_LEN or c.count("…") > 1:
        continue
    # dairesel tanımı ele: tanım cevabın köküyle başlıyorsa (ör. "Abartmak durumu")
    stem = deaccent(w)[:max(4, len(w) - 1)]
    if deaccent(c).lower().startswith(stem):
        continue
    d = "k" if rank < EASY_MAX else ("o" if rank < MED_MAX else "z")
    seen[w] = {"w": tr_upper(w), "c": c, "d": d, "_r": rank, "_L": len(w)}

# ---------------------------------------------------------------- kovalar + cap
buckets = {}   # (L,d) -> list
for o in seen.values():
    buckets.setdefault((o["_L"], o["d"]), []).append(o)

out = []
for (L, d), lst in buckets.items():
    lst.sort(key=lambda x: x["_r"])          # en yaygın önce
    for o in lst[:CAP_PER_BUCKET]:
        out.append({"w": o["w"], "c": o["c"], "d": o["d"]})

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
import itertools
for L in (4, 7, 10):
    for d in ("k","o","z"):
        ex = next((x for x in out if len(x["w"])==L and x["d"]==d), None)
        if ex: print(f"  [{L}h/{d}] {ex['w']}: {ex['c'][:70]}")
