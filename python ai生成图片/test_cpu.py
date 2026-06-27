import os
import sys
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

def log(msg):
    with open("output_log.txt", "a") as f:
        f.write(msg + "\n")

log("Starting...")

try:
    from diffusers import StableDiffusionPipeline
    log("Imported diffusers")
    
    import torch
    log(f"Imported torch, version: {torch.__version__}")
    log(f"CUDA available: {torch.cuda.is_available()}")
    
    log("Loading model...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        safety_checker=None
    )
    log("Pipeline created")
    
    pipe.to("cpu")
    log("Pipeline moved to CPU")
    
    pipe.enable_attention_slicing("max")
    log("Attention slicing enabled")
    
    log("Model loaded successfully!")
    
    prompt = "a cat"
    log(f"Generating image for: {prompt}")
    
    image = pipe(
        prompt=prompt,
        num_inference_steps=10,
        height=512,
        width=512,
        guidance_scale=7.5
    ).images[0]
    
    image.save("test_output.png")
    log("Image saved as test_output.png")
    
except Exception as e:
    log(f"Error: {str(e)}")
    import traceback
    log(f"Traceback: {traceback.format_exc()}")
