import sys
print('STEP 1', flush=True)
import torch
print('torch:', torch.__version__, flush=True)
print('STEP 2', flush=True)
import torchvision
print('torchvision:', torchvision.__version__, flush=True)
print('STEP 3', flush=True)
from transformers import CLIPImageProcessor
print('CLIPImageProcessor OK', flush=True)
print('STEP 4', flush=True)
from diffusers import StableDiffusionPipeline
print('StableDiffusionPipeline OK', flush=True)
print('ALL IMPORTS OK', flush=True)
