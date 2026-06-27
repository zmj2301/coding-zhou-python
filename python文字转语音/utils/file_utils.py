import os
from pathlib import Path


def ensure_dir_exists(dir_path):
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    return dir_path


def get_unique_filename(base_path, extension):
    base = Path(base_path)
    counter = 1
    while True:
        if counter == 1:
            new_path = f"{base}.{extension}"
        else:
            new_path = f"{base}_{counter}.{extension}"
        
        if not Path(new_path).exists():
            return new_path
        counter += 1
