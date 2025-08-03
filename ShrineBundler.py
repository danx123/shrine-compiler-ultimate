import zipfile, os
from datetime import datetime

def bundle_glyphs(glyph_folder, manifest_path, output_folder="output/bundle"):
    if not os.path.exists(glyph_folder):
        print("⛔ Folder glyph tidak ditemukan.")
        return

    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_name = f"shrine_bundle_{timestamp}.pak"
    bundle_path = os.path.join(output_folder, bundle_name)

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as shrine_zip:
        # Tambah semua glyph
        for root, _, files in os.walk(glyph_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, glyph_folder)
                shrine_zip.write(file_path, arcname)
                print(f"📦 Bundling: {file}")

        # Tambahkan manifest
        if os.path.exists(manifest_path):
            shrine_zip.write(manifest_path, arcname="manifest_glyph.txt")
            print("📜 Manifest ditambahkan.")

    print(f"\n✅ Bundle sukses: {bundle_path}")

if __name__ == "__main__":
    bundle_glyphs("output/.glyphs", "manifest_glyph.txt")