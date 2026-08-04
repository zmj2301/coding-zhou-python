"""Check PVZ image directories"""
import os

base = 'e:\\coding-zhou\\Python\\web-games\\pvz_tmp\\game\\images'
for root, dirs, files in os.walk(base):
    pngs = [f for f in files if f.endswith(('.png', '.jpg', '.gif'))]
    psds = [f for f in files if f.endswith('.psd')]
    if psds or pngs or root.count(os.sep) - base.count(os.sep) <= 1:
        rel = os.path.relpath(root, base)
        print(f"{rel}/  PNG={len(pngs):3d}  PSD={len(psds):3d}")
        if pngs:
            print(f"  PNGs: {', '.join(pngs[:5])}")
        if psds:
            print(f"  PSDs: {', '.join(psds[:5])}")
