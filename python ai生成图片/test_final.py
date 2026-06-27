import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

f = open("final_log.txt", "w")

try:
    f.write("1. Starting...\n")
    f.flush()

    import torch
    f.write(f"2. torch OK, version={torch.__version__}\n")
    f.flush()

    f.write("3. Before diffusers...\n")
    f.flush()
    
    import diffusers
    f.write(f"4. diffusers OK, version={diffusers.__version__}\n")
    f.flush()

    f.write("5. Before StableDiffusionPipeline...\n")
    f.flush()
    
    from diffusers import StableDiffusionPipeline
    f.write("6. StableDiffusionPipeline OK!\n")
    f.flush()

    f.write("All OK!\n")
    
except Exception as e:
    f.write(f"ERROR: {str(e)}\n")
    
f.close()
