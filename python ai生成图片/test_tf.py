import sys
sys.stdout = open("e:/coding-zhou/Python/python ai生成图片/out.txt", "w", buffering=1)
sys.stderr = sys.stdout
print('start', flush=True)
import transformers
print('tf', transformers.__version__, flush=True)
from transformers import CLIPImageProcessor
print('CLIP OK', flush=True)
from diffusers import StableDiffusionPipeline
print('diffusers OK', flush=True)
print('ALL OK', flush=True)
