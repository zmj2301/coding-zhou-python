import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

print("1. Importing...", flush=True)
from diffusers import StableDiffusionPipeline
import torch

print("2. Loading lightweight model...", flush=True)
pipe = StableDiffusionPipeline.from_pretrained(
    "sd-dreambooth-library/marvel-v1",
    torch_dtype=torch.float32,
    low_cpu_mem_usage=True,
    safety_checker=None,
    variant="fp16"
)
pipe.to("cpu")
pipe.enable_attention_slicing("max")

print("3. Generating image...", flush=True)
image = pipe(
    prompt="a beautiful cat",
    num_inference_steps=15,
    height=512,
    width=512
).images[0]

image.save("output_light.png")
print("4. Image saved!", flush=True)
