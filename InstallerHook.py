import subprocess, os
from ShrineBundler import bundle_glyphs

GLYPH_FOLDER = "output/.glyphs"
MANIFEST_PATH = "manifest_glyph.txt"
INSTALLER_CMD = ["pyinstaller", "main.py", "--onefile", "--noconsole"]

def run_hook():
    print("⚙️ Memulai pre-processing ritual...")

    # Cek glyph sudah terisi
    if not os.path.exists(GLYPH_FOLDER) or not os.listdir(GLYPH_FOLDER):
        print("⛔ Glyph folder kosong. Jalankan ShrineCompiler dulu.")
        return

    # Bundling glyph & manifest
    bundle_glyphs(GLYPH_FOLDER, MANIFEST_PATH)
    print("✅ Glyph bundling selesai.")

    # Eksekusi installer tool
    try:
        print("📦 Memulai packing installer...")
        subprocess.run(INSTALLER_CMD, check=True)
        print("🚀 Installer sukses dibangun!")
    except Exception as e:
        print(f"❌ Gagal saat packing: {e}")

if __name__ == "__main__":
    run_hook()