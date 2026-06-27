import os
import sys
import threading
from datetime import datetime

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

print("1. Importing diffusers...", flush=True)
from diffusers import StableDiffusionPipeline
print("2. Importing torch...", flush=True)
import torch

print("3. Initializing pipeline...", flush=True)

_pipe = None
_pipe_lock = threading.Lock()

def get_pipeline():
    global _pipe
    if _pipe is None:
        with _pipe_lock:
            if _pipe is None:
                model_id = "runwayml/stable-diffusion-v1-5"
                print(f"4. Loading model: {model_id}...", flush=True)
                _pipe = StableDiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    safety_checker=None
                )
                print("5. Moving to CPU...", flush=True)
                _pipe.to("cpu")
                print("6. Enabling attention slicing...", flush=True)
                _pipe.enable_attention_slicing("max")
                print("7. Pipeline ready!", flush=True)
    return _pipe

def generate_image(prompt, negative_prompt="模糊,低画质,畸形,水印", steps=20, size=(512,512), output_prefix="output"):
    pipe = get_pipeline()

    print(f"8. Generating image for: {prompt}", flush=True)
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=steps,
        height=size[0],
        width=size[1],
        guidance_scale=7.5
    ).images[0]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{output_prefix}_{timestamp}.png"
    image.save(save_name)
    print(f"9. Image saved as {save_name}, size: {image.size}", flush=True)
    return image

if __name__ == "__main__":
    text = "治愈系田园风景，日落，小溪，向日葵，高清写实，细腻光影"
    generate_image(prompt=text)
