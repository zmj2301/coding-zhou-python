import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

f = open("import_log.txt", "w")

f.write("Step 1: before torch import\n")
f.flush()

import torch
f.write(f"Step 2: torch imported, version={torch.__version__}\n")
f.flush()

f.write("Step 3: before diffusers import\n")
f.flush()

from diffusers import StableDiffusionPipeline
f.write("Step 4: diffusers imported\n")
f.flush()

f.write("All imports OK!\n")
f.close()
