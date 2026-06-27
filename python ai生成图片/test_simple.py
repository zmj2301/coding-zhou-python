import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

f = open("simple_log.txt", "w")

f.write("1. Starting...\n")
f.flush()

import torch
f.write(f"2. torch OK, version={torch.__version__}\n")
f.flush()

import diffusers
f.write(f"3. diffusers OK, version={diffusers.__version__}\n")
f.flush()

f.write("All OK!\n")
f.close()
