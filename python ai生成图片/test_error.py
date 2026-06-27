import os
import sys
import traceback
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

sys.stderr = open("error_log.txt", "w")

try:
    print("1. Starting...", file=sys.stderr)
    sys.stderr.flush()

    import torch
    print(f"2. torch OK, version={torch.__version__}", file=sys.stderr)
    sys.stderr.flush()

    print("3. Before diffusers...", file=sys.stderr)
    sys.stderr.flush()
    
    import diffusers
    print(f"4. diffusers OK, version={diffusers.__version__}", file=sys.stderr)
    sys.stderr.flush()

    print("5. Before StableDiffusionPipeline...", file=sys.stderr)
    sys.stderr.flush()
    
    from diffusers import StableDiffusionPipeline
    print("6. StableDiffusionPipeline OK!", file=sys.stderr)
    sys.stderr.flush()

    print("All OK!", file=sys.stderr)
    
except Exception as e:
    print(f"ERROR: {str(e)}", file=sys.stderr)
    print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
    
sys.stderr.close()
