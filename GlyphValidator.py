import os, hashlib
from datetime import datetime

GLYPH_FOLDER = "output/.glyphs"
MANIFEST_PATH = "manifest_glyph.txt"

def hash_file(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def validate_glyphs():
    print(f"🔍 Memulai validasi shrine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if not os.path.exists(GLYPH_FOLDER):
        print("⛔ Glyph folder tidak ditemukan.")
        return

    if not os.path.exists(MANIFEST_PATH):
        print("⛔ Manifest tidak ditemukan.")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as manifest:
        lines = [l.strip() for l in manifest.readlines() if l.strip().endswith(".pyc")]
        print(f"📜 Jumlah glyph di manifest: {len(lines)}")

        match = 0
        for path in lines:
            if os.path.exists(path):
                h = hash_file(path)
                print(f"✅ {os.path.basename(path)} → {h}")
                match += 1
            else:
                print(f"❌ Tidak ditemukan: {path}")

        print(f"\n🔐 Total tervalidasi: {match}/{len(lines)} glyph")

if __name__ == "__main__":
    validate_glyphs()